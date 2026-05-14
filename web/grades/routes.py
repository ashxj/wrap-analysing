from datetime import datetime, timezone
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required

from extensions import db
from models import Grade
from grades.processor import (
    compute_subject_stats,
    find_weak_subjects,
    find_weak_lesson_types,
    sort_grades_by_date,
    grades_to_dicts,
    save_grades_to_db,
    weekly_average_trend,
)
from grades.calculator import calculate_required_grades, generate_scenario_table

grades_bp = Blueprint("grades", __name__)


def _user_grades_dicts():
    db_grades = Grade.query.filter_by(user_id=current_user.id).all()
    return grades_to_dicts(db_grades)


@grades_bp.route("/grades")
@login_required
def grades_list():
    grades = sort_grades_by_date(_user_grades_dicts())
    return render_template("grades.html", grades=grades)


@grades_bp.route("/subjects")
@login_required
def subjects():
    threshold = current_app.config["WEAK_GRADE_THRESHOLD"]
    grades = _user_grades_dicts()
    stats = compute_subject_stats(grades)
    weak = {s["subject"] for s in find_weak_subjects(stats, threshold)}
    for stat in stats:
        stat["is_weak"] = stat["subject"] in weak
        stat["lesson_type_breakdown"] = find_weak_lesson_types(grades, stat["subject"])
        stat["sorted_grades"] = sort_grades_by_date(stat["grades"])
    return render_template("subjects.html", stats=stats, threshold=threshold)


@grades_bp.route("/calculator", methods=["GET", "POST"])
@login_required
def calculator():
    grades = _user_grades_dicts()
    stats = compute_subject_stats(grades)
    subjects = [s["subject"] for s in stats]

    result = None
    scenario_table = None
    selected_subject = None
    desired_avg = None
    remaining_works = None

    if request.method == "POST":
        selected_subject = request.form.get("subject", "").strip()
        try:
            desired_avg = float(request.form.get("desired_avg", "7"))
            remaining_works = int(request.form.get("remaining_works", "5"))
        except (ValueError, TypeError):
            flash("Please enter valid numeric values.", "error")
            return render_template("calculator.html", stats=stats, subjects=subjects)

        desired_avg = max(1.0, min(10.0, desired_avg))
        remaining_works = max(1, min(50, remaining_works))
        if desired_avg == int(desired_avg):
            desired_avg = int(desired_avg)

        subject_stat = next((s for s in stats if s["subject"] == selected_subject), None)
        if not subject_stat:
            flash("Subject not found.", "error")
            return render_template("calculator.html", stats=stats, subjects=subjects)

        numeric_grades = []
        for g in subject_stat["grades"]:
            v = g.get("value")
            if v is not None:
                try:
                    val = float(str(v).replace(",", "."))
                    if 1 <= val <= 10:
                        numeric_grades.append(val)
                except ValueError:
                    pass

        result = calculate_required_grades(numeric_grades, desired_avg, remaining_works)
        scenario_table = generate_scenario_table(numeric_grades, desired_avg, max_works=20)

    return render_template(
        "calculator.html",
        stats=stats,
        subjects=subjects,
        result=result,
        scenario_table=scenario_table,
        selected_subject=selected_subject,
        desired_avg=desired_avg,
        remaining_works=remaining_works,
    )


@grades_bp.route("/sync", methods=["POST"])
@login_required
def sync():
    from auth.oidc import token_expired, fetch_grades_sync, api_fetch, login_to_eklase
    from auth.routes import decrypt_password, encrypt_password
    import asyncio

    user = current_user._get_current_object()
    expires_at_ms = None
    if user.token_expires_at:
        expires_at_ms = user.token_expires_at.timestamp() * 1000

    if token_expired(expires_at_ms):
        try:
            password = decrypt_password(user.eklase_password_encrypted)
            cdp = current_app.config["OBSCURA_CDP_ENDPOINT"]
            result = asyncio.run(login_to_eklase(user.eklase_username, password, user.profile_id, cdp))
            tokens = result["tokens"]
            user.access_token = tokens["access_token"]
            user.token_expires_at = datetime.fromtimestamp(tokens["expires_at"] / 1000, tz=timezone.utc)
            db.session.commit()
        except Exception as e:
            flash(f"Re-authentication failed: {e}", "error")
            return redirect(url_for("dashboard.index"))

    try:
        data = fetch_grades_sync(user.access_token)
        save_grades_to_db(user.id, data["grades"])
        user.last_synced_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("Grades updated successfully.", "success")
    except Exception as e:
        flash(f"Failed to fetch grades: {e}", "error")

    return redirect(url_for("dashboard.index"))
