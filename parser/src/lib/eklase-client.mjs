import crypto from "node:crypto";
import { chromium } from "playwright-core";
import { normalizeEvaluations } from "./grades.mjs";

export const FAMILY_API_BASE = "https://family.e-klase.lv/api";
export const ISSUER = "https://auth.e-klase.lv/realms/family";
export const AUTHORIZATION_ENDPOINT = `${ISSUER}/protocol/openid-connect/auth`;
export const TOKEN_ENDPOINT = `${ISSUER}/protocol/openid-connect/token`;
export const CLIENT_ID = "web";
export const REDIRECT_URI = "https://family.e-klase.lv/redirect.html";

export async function loginToEKlase({
  username,
  password,
  profileId = "",
  cdpEndpoint = "http://127.0.0.1:9222",
}) {
  const browser = await connectToObscura(cdpEndpoint);
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const navigationLog = [];
  page.on("framenavigated", (frame) => {
    if (frame === page.mainFrame()) navigationLog.push(frame.url());
  });

  try {
    const pkce = createPkce();
    await page.goto(buildAuthorizationUrl(pkce), { waitUntil: "domcontentloaded" });
    await completeLoginForm(page, username, password);

    const redirectedUrl = await waitForRedirectCode(page, context, navigationLog);
    const code = extractAuthorizationCode(redirectedUrl, pkce.state);
    const tokens = await exchangeCodeForTokens(code, pkce.codeVerifier);
    const tokensWithExpiry = addTokenExpiry(tokens);

    const profiles = await apiFetch("/user/profiles", tokensWithExpiry.access_token);
    const selectedProfile = selectProfile(profiles, profileId);
    const switchResult = await apiFetch(
      "/user/profiles/switch",
      tokensWithExpiry.access_token,
      {
        method: "POST",
        body: JSON.stringify({ profileId: selectedProfile.profileId }),
      }
    );

    const selected = {
      profileId: selectedProfile.profileId,
      firstName: selectedProfile.firstName,
      lastName: selectedProfile.lastName,
      schoolName: selectedProfile.school?.name || selectedProfile.schoolName || null,
      className: selectedProfile.class?.name || selectedProfile.className || null,
      switchResult,
    };

    return { tokens: tokensWithExpiry, profiles, selectedProfile: selected };
  } catch (err) {
    const debug = {
      error: err instanceof Error ? err.message : String(err),
      url: page.url(),
      title: await page.title().catch(() => null),
      navigations: navigationLog,
      cookies: await context.cookies().catch(() => []),
      html: await page.content().catch(() => null),
    };
    throw Object.assign(err, { debug });
  } finally {
    await browser.close();
  }
}

export async function fetchGrades(accessToken) {
  const summary = await apiFetch("/evaluations/summary", accessToken);
  return {
    raw: summary,
    grades: normalizeEvaluations(summary),
  };
}

export function tokenExpired(tokens) {
  return !tokens?.access_token || !tokens.expires_at || Date.now() > tokens.expires_at - 30_000;
}

export async function apiFetch(pathname, accessToken, options = {}) {
  const res = await fetch(`${FAMILY_API_BASE}${pathname}`, {
    method: options.method || "GET",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(options.headers || {}),
    },
    body: options.body,
  });

  const text = await res.text();
  if (!res.ok) {
    throw new Error(`API ${pathname} failed: ${res.status} ${text}`);
  }
  return text ? JSON.parse(text) : null;
}

async function connectToObscura(cdpEndpoint) {
  try {
    return await chromium.connectOverCDP(cdpEndpoint);
  } catch {
    throw new Error(
      `Failed to connect to Obscura CDP at ${cdpEndpoint}. Start server with: bash scripts/start-obscura.sh`
    );
  }
}

function createPkce() {
  const codeVerifier = base64Url(crypto.randomBytes(32));
  const codeChallenge = base64Url(crypto.createHash("sha256").update(codeVerifier).digest());
  return {
    codeVerifier,
    codeChallenge,
    state: crypto.randomUUID(),
    nonce: base64Url(crypto.randomBytes(24)),
  };
}

function base64Url(buf) {
  return buf
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function buildAuthorizationUrl(pkce) {
  const url = new URL(AUTHORIZATION_ENDPOINT);
  url.searchParams.set("scope", "openid");
  url.searchParams.set("response_type", "code");
  url.searchParams.set("client_id", CLIENT_ID);
  url.searchParams.set("redirect_uri", REDIRECT_URI);
  url.searchParams.set("state", pkce.state);
  url.searchParams.set("nonce", pkce.nonce);
  url.searchParams.set("ui_locales", "lv");
  url.searchParams.set("code_challenge", pkce.codeChallenge);
  url.searchParams.set("code_challenge_method", "S256");
  return url.toString();
}

async function completeLoginForm(page, username, password) {
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
  if (page.url().startsWith(REDIRECT_URI)) return;

  const hasFields = await page.evaluate(() =>
    Boolean(
      document.querySelector("#username, input[name='username'], input[type='text']") &&
        document.querySelector("#password, input[name='password'], input[type='password']") &&
        document.querySelector("form")
    )
  );

  if (!hasFields) {
    throw new Error(`Keycloak login fields not found on ${page.url()}`);
  }

  await page.evaluate(
    ({ username: userValue, password: passValue }) => {
      const user = document.querySelector("#username, input[name='username'], input[type='text']");
      const pass = document.querySelector("#password, input[name='password'], input[type='password']");
      const form = document.querySelector("form");
      user.value = userValue;
      pass.value = passValue;
      user.dispatchEvent(new Event("input", { bubbles: true }));
      pass.dispatchEvent(new Event("input", { bubbles: true }));
      form.submit();
    },
    { username, password }
  );
}

async function waitForRedirectCode(page, context, navigationLog) {
  for (let i = 0; i < 80; i += 1) {
    const currentUrl = page.url();
    const loggedRedirect = navigationLog.find(isCodeRedirect);
    if (loggedRedirect) return loggedRedirect;
    if (isCodeRedirect(currentUrl)) return currentUrl;

    if (currentUrl.startsWith(REDIRECT_URI) && new URL(currentUrl).searchParams.has("error")) {
      throw new Error(`OIDC redirect returned error: ${currentUrl}`);
    }

    if (currentUrl.includes("/protocol/openid-connect/authenticate")) {
      const isAuthenticated = await page
        .evaluate(() => document.documentElement.outerHTML.includes("isAuthSuccessful = true"))
        .catch(() => false);
      if (isAuthenticated) {
        const location = await getAuthenticateForwardLocation(context);
        if (isCodeRedirect(location)) return location;
        if (location) navigationLog.push(location);
      }
    }

    await page.waitForTimeout(500);
  }
  throw new Error(
    `Timed out waiting for OIDC code. Last URL: ${page.url()}. Navigations: ${navigationLog.join(" -> ")}`
  );
}

function isCodeRedirect(value) {
  try {
    return value?.startsWith(REDIRECT_URI) && new URL(value).searchParams.has("code");
  } catch {
    return false;
  }
}

async function getAuthenticateForwardLocation(context) {
  const authCookie = (await context.cookies()).find((cookie) => cookie.domain === "auth.e-klase.lv");
  if (!authCookie) {
    throw new Error("Auth cookie missing before authenticate-forward");
  }

  const res = await fetch(`${ISSUER}/protocol/openid-connect/authenticate-forward`, {
    redirect: "manual",
    headers: {
      Cookie: `${authCookie.name}=${authCookie.value}`,
    },
  });

  const location = res.headers.get("location");
  if (res.status < 300 || res.status >= 400 || !location) {
    const text = await res.text();
    throw new Error(`authenticate-forward failed: ${res.status} ${text.slice(0, 300)}`);
  }
  return location;
}

function extractAuthorizationCode(redirectedUrl, expectedState) {
  const url = new URL(redirectedUrl);
  if (url.searchParams.get("state") !== expectedState) {
    throw new Error("OIDC state mismatch");
  }
  const code = url.searchParams.get("code");
  if (!code) throw new Error("OIDC authorization code missing");
  return code;
}

async function exchangeCodeForTokens(code, codeVerifier) {
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    code,
    code_verifier: codeVerifier,
  });

  const res = await fetch(TOKEN_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  const text = await res.text();
  if (!res.ok) {
    throw new Error(`Token exchange failed: ${res.status} ${text}`);
  }
  return JSON.parse(text);
}

function addTokenExpiry(tokens) {
  return {
    ...tokens,
    expires_at: Date.now() + (tokens.expires_in || 0) * 1000,
  };
}

function selectProfile(profiles, configuredProfileId = "") {
  const activeProfiles = profiles.activeProfiles || [];
  const profile =
    activeProfiles.find((item) => item.profileId === configuredProfileId) ||
    activeProfiles[0];

  if (!profile) {
    throw new Error("No active profiles returned by /user/profiles");
  }
  return profile;
}
