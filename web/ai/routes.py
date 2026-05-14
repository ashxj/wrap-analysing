from flask import Blueprint, current_app, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required

from grades.processor import compute_subject_stats, find_weak_subjects, grades_to_dicts
from models import Grade, Recommendation
from ai.advisor import get_recommendations, refresh_recommendations

ai_bp = Blueprint("ai", __name__)


def _user_grades_dicts():
    db_grades = Grade.query.filter_by(user_id=current_user.id).all()
    return grades_to_dicts(db_grades)


def _get_relevant_topics(grades: list, subject: str, limit: int = 12) -> list:
    """Return unique lesson topics for a subject, lowest-graded first."""
    import re

    def _parse_num(value):
        if value is None:
            return None
        text = str(value).strip().replace(",", ".")
        if not re.match(r"^\d+(\.\d+)?$", text):
            return None
        try:
            v = float(text)
            return v if 1 <= v <= 10 else None
        except ValueError:
            return None

    subject_grades = [g for g in grades if g.get("subject") == subject]

    # Sort: numeric grades ascending (weakest first), non-numeric last
    def sort_key(g):
        n = _parse_num(g.get("value"))
        return (0, n) if n is not None else (1, 0)

    sorted_grades = sorted(subject_grades, key=sort_key)

    seen: set = set()
    topics: list = []
    for g in sorted_grades:
        topic = (g.get("lesson_topic") or "").strip()
        if topic and topic not in seen:
            seen.add(topic)
            topics.append(topic)
        if len(topics) >= limit:
            break
    return topics


@ai_bp.route("/recommendations")
@login_required
def recommendations():
    threshold = current_app.config["WEAK_GRADE_THRESHOLD"]
    api_key = current_app.config["ANTHROPIC_API_KEY"]
    grades = _user_grades_dicts()
    stats = compute_subject_stats(grades)
    weak_subject_names = {s["subject"] for s in find_weak_subjects(stats, threshold)}

    subjects_with_recs = []
    for stat in stats:
        topics = _get_relevant_topics(grades, stat["subject"])
        recs = get_recommendations(
            user_id=current_user.id,
            subject=stat["subject"],
            class_name=current_user.class_name,
            topics=topics,
            api_key=api_key,
        )
        subjects_with_recs.append({
            "subject": stat["subject"],
            "average": stat["average"],
            "is_weak": stat["subject"] in weak_subject_names,
            "topics": topics,
            "recommendations": recs,
        })

    subjects_with_recs.sort(key=lambda x: (not x["is_weak"], x["subject"]))
    return render_template("recommendations.html", subjects=subjects_with_recs)


@ai_bp.route("/recommendations/refresh/<path:subject>", methods=["POST"])
@login_required
def refresh(subject):
    api_key = current_app.config["ANTHROPIC_API_KEY"]
    grades = _user_grades_dicts()
    topics = _get_relevant_topics(grades, subject)

    try:
        refresh_recommendations(
            user_id=current_user.id,
            subject=subject,
            class_name=current_user.class_name,
            topics=topics,
            api_key=api_key,
        )
        flash(f"Recommendations for «{subject}» updated.", "success")
    except Exception as e:
        flash(f"Failed to update recommendations: {e}", "error")

    return redirect(url_for("ai.recommendations"))
