import asyncio
import base64
import hashlib
import json
import os
import secrets
import urllib.parse
from datetime import datetime, timezone

import requests
from playwright.async_api import async_playwright

FAMILY_API_BASE = "https://family.e-klase.lv/api"
ISSUER = "https://auth.e-klase.lv/realms/family"
AUTHORIZATION_ENDPOINT = f"{ISSUER}/protocol/openid-connect/auth"
TOKEN_ENDPOINT = f"{ISSUER}/protocol/openid-connect/token"
AUTHENTICATE_FORWARD = f"{ISSUER}/protocol/openid-connect/authenticate-forward"
CLIENT_ID = "web"
REDIRECT_URI = "https://family.e-klase.lv/redirect.html"


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _create_pkce():
    code_verifier = _base64url(os.urandom(32))
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = _base64url(digest)
    return {
        "code_verifier": code_verifier,
        "code_challenge": code_challenge,
        "state": secrets.token_urlsafe(16),
        "nonce": _base64url(os.urandom(24)),
    }


def _build_authorization_url(pkce: dict) -> str:
    params = {
        "scope": "openid",
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "state": pkce["state"],
        "nonce": pkce["nonce"],
        "ui_locales": "lv",
        "code_challenge": pkce["code_challenge"],
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urllib.parse.urlencode(params)}"


def _is_code_redirect(url: str) -> bool:
    try:
        if not url.startswith(REDIRECT_URI):
            return False
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        return "code" in qs
    except Exception:
        return False


def _extract_code(url: str, expected_state: str) -> str:
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    state = qs.get("state", [None])[0]
    if state != expected_state:
        raise ValueError(f"OIDC state mismatch: expected {expected_state}, got {state}")
    code = qs.get("code", [None])[0]
    if not code:
        raise ValueError("OIDC authorization code missing from redirect")
    return code


def _exchange_code(code: str, code_verifier: str) -> dict:
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "code_verifier": code_verifier,
    }
    resp = requests.post(TOKEN_ENDPOINT, data=data, timeout=30)
    if not resp.ok:
        raise ValueError(f"Token exchange failed: {resp.status_code} {resp.text}")
    return resp.json()


def _add_expiry(tokens: dict) -> dict:
    tokens = dict(tokens)
    tokens["expires_at"] = (
        datetime.now(timezone.utc).timestamp() * 1000 + (tokens.get("expires_in", 0)) * 1000
    )
    return tokens


def api_fetch(path: str, access_token: str, method: str = "GET", body=None) -> dict:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    resp = requests.request(
        method,
        f"{FAMILY_API_BASE}{path}",
        headers=headers,
        json=body,
        timeout=30,
    )
    if not resp.ok:
        raise ValueError(f"API {path} failed: {resp.status_code} {resp.text}")
    text = resp.text.strip()
    return json.loads(text) if text else None


def token_expired(expires_at_ms: float | None) -> bool:
    if not expires_at_ms:
        return True
    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    return now_ms > expires_at_ms - 30_000


def _select_profile(profiles: dict, configured_profile_id: str = "") -> dict:
    active = profiles.get("activeProfiles", [])
    if not active:
        raise ValueError("No active profiles returned by /user/profiles")
    if configured_profile_id:
        match = next((p for p in active if p.get("profileId") == configured_profile_id), None)
        if match:
            return match
    return active[0]


async def _get_authenticate_forward_location(cookies: list) -> str | None:
    auth_cookie = next((c for c in cookies if c.get("domain") == "auth.e-klase.lv"), None)
    if not auth_cookie:
        return None

    def _do_request():
        resp = requests.get(
            AUTHENTICATE_FORWARD,
            headers={"Cookie": f"{auth_cookie['name']}={auth_cookie['value']}"},
            allow_redirects=False,
            timeout=15,
        )
        if 300 <= resp.status_code < 400:
            return resp.headers.get("Location")
        return None

    return await asyncio.to_thread(_do_request)


async def _get_browser(p, cdp_endpoint: str):
    """Connect to Obscura CDP if available, otherwise launch a local Chromium instance."""
    try:
        browser = await p.chromium.connect_over_cdp(cdp_endpoint)
        return browser, False
    except Exception:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        return browser, True


async def login_to_eklase(username: str, password: str, profile_id: str = "", cdp_endpoint: str = "http://127.0.0.1:9222") -> dict:
    pkce = _create_pkce()
    auth_url = _build_authorization_url(pkce)
    navigation_log = []
    redirect_url = None

    async with async_playwright() as p:
        browser, _own = await _get_browser(p, cdp_endpoint)

        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        def _on_nav(frame):
            if frame == page.main_frame:
                navigation_log.append(frame.url)
        page.on("framenavigated", _on_nav)

        try:
            await page.goto(auth_url, wait_until="domcontentloaded")

            try:
                await page.wait_for_load_state("networkidle", timeout=20_000)
            except Exception:
                pass

            current = page.url
            if not current.startswith(REDIRECT_URI):
                has_fields = await page.evaluate("""() =>
                    Boolean(
                        document.querySelector('#username, input[name="username"], input[type="text"]') &&
                        document.querySelector('#password, input[name="password"], input[type="password"]') &&
                        document.querySelector('form')
                    )
                """)
                if not has_fields:
                    raise ValueError(f"Keycloak login fields not found on {page.url}")

                await page.evaluate(
                    """({u, pw}) => {
                        const user = document.querySelector('#username, input[name="username"], input[type="text"]');
                        const pass = document.querySelector('#password, input[name="password"], input[type="password"]');
                        user.value = u;
                        pass.value = pw;
                        user.dispatchEvent(new Event('input', {bubbles: true}));
                        pass.dispatchEvent(new Event('input', {bubbles: true}));
                        document.querySelector('form').submit();
                    }""",
                    {"u": username, "pw": password},
                )

            for _ in range(80):
                cur = page.url
                logged = next((u for u in navigation_log if _is_code_redirect(u)), None)
                if logged:
                    redirect_url = logged
                    break
                if _is_code_redirect(cur):
                    redirect_url = cur
                    break
                if cur.startswith(REDIRECT_URI):
                    parsed = urllib.parse.urlparse(cur)
                    if "error" in urllib.parse.parse_qs(parsed.query):
                        raise ValueError(f"OIDC redirect returned error: {cur}")

                if "/protocol/openid-connect/authenticate" in cur:
                    try:
                        is_auth = await page.evaluate(
                            "() => document.documentElement.outerHTML.includes('isAuthSuccessful = true')"
                        )
                    except Exception:
                        is_auth = False
                    if is_auth:
                        cookies = await context.cookies()
                        location = await _get_authenticate_forward_location([
                            {"name": c["name"], "value": c["value"], "domain": c["domain"]} for c in cookies
                        ])
                        if location and _is_code_redirect(location):
                            redirect_url = location
                            break
                        if location:
                            navigation_log.append(location)

                await page.wait_for_timeout(500)

            if not redirect_url:
                raise ValueError(
                    f"Timed out waiting for OIDC code. Last URL: {page.url}. Navigations: {' -> '.join(navigation_log[-5:])}"
                )

        except Exception as err:
            html = await page.content()
            raise ValueError(f"{err} | HTML snippet: {html[:500]}") from err
        finally:
            await browser.close()

    code = _extract_code(redirect_url, pkce["state"])
    raw_tokens = await asyncio.to_thread(_exchange_code, code, pkce["code_verifier"])
    tokens = _add_expiry(raw_tokens)

    profiles = await asyncio.to_thread(api_fetch, "/user/profiles", tokens["access_token"])
    selected = _select_profile(profiles, profile_id)
    switch_result = await asyncio.to_thread(
        api_fetch,
        "/user/profiles/switch",
        tokens["access_token"],
        "POST",
        {"profileId": selected["profileId"]},
    )

    return {
        "tokens": tokens,
        "profiles": profiles,
        "selectedProfile": {
            "profileId": selected.get("profileId"),
            "firstName": selected.get("firstName"),
            "lastName": selected.get("lastName"),
            "schoolName": selected.get("school", {}).get("name") or selected.get("schoolName"),
            "className": selected.get("class", {}).get("name") or selected.get("className"),
            "switchResult": switch_result,
        },
    }


def fetch_grades_sync(access_token: str) -> dict:
    from grades.processor import normalize_evaluations
    summary = api_fetch("/evaluations/summary", access_token)
    return {"raw": summary, "grades": normalize_evaluations(summary)}
