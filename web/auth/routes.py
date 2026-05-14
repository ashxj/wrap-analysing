import asyncio
import json
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


def _get_fernet():
    key = current_app.config.get("FERNET_KEY", "")
    if not key:
        key = Fernet.generate_key().decode()
        current_app.config["FERNET_KEY"] = key
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_password(password: str) -> str:
    return _get_fernet().encrypt(password.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        profile_id = request.form.get("profile_id", "").strip()

        if not username or not password:
            flash("Please enter your username and password.", "error")
            return render_template("login.html")

        from auth.oidc import login_to_eklase
        cdp = current_app.config["OBSCURA_CDP_ENDPOINT"]

        try:
            result = asyncio.run(login_to_eklase(username, password, profile_id, cdp))
        except Exception as e:
            flash(f"Login error: {e}", "error")
            return render_template("login.html")

        tokens = result["tokens"]
        selected = result["selectedProfile"]

        user = User.query.filter_by(eklase_username=username).first()
        if not user:
            user = User(eklase_username=username)
            db.session.add(user)

        user.eklase_password_encrypted = encrypt_password(password)
        user.profile_id = selected.get("profileId", "")
        user.profile = {
            "firstName": selected.get("firstName", ""),
            "lastName": selected.get("lastName", ""),
            "schoolName": selected.get("schoolName", ""),
            "className": selected.get("className", ""),
        }
        user.access_token = tokens["access_token"]
        expires_at_ms = tokens.get("expires_at", 0)
        user.token_expires_at = datetime.fromtimestamp(expires_at_ms / 1000, tz=timezone.utc)
        db.session.commit()

        _sync_grades_for_user(user, tokens["access_token"])

        login_user(user, remember=True)
        flash("Logged in successfully!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


def _sync_grades_for_user(user: User, access_token: str):
    from auth.oidc import fetch_grades_sync
    from grades.processor import save_grades_to_db

    try:
        data = fetch_grades_sync(access_token)
        save_grades_to_db(user.id, data["grades"])
        user.last_synced_at = datetime.now(timezone.utc)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Grade sync failed for user {user.id}: {e}")
