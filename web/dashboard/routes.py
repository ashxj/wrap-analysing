import json
from flask import Blueprint, render_template, current_app
from flask_login import current_user, login_required

from models import Grade
from grades.processor import (
    compute_subject_stats,
    find_weak_subjects,
    sort_grades_by_date,
    weekly_average_trend,
    grades_to_dicts,
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    threshold = current_app.config["WEAK_GRADE_THRESHOLD"]
    db_grades = Grade.query.filter_by(user_id=current_user.id).all()
    grades = grades_to_dicts(db_grades)

    stats = compute_subject_stats(grades)
    weak = find_weak_subjects(stats, threshold)
    recent = sort_grades_by_date(grades)[:10]
    trend = weekly_average_trend(grades)

    overall_nums = [
        float(str(g["value"]).replace(",", "."))
        for g in grades
        if g.get("value") is not None
        and str(g["value"]).replace(",", ".").replace(".", "", 1).isdigit()
        and 1 <= float(str(g["value"]).replace(",", ".")) <= 10
    ]
    overall_avg = round(sum(overall_nums) / len(overall_nums), 2) if overall_nums else None

    best_subject = max(stats, key=lambda s: s["average"] or 0, default=None)
    worst_subject = min(
        (s for s in stats if s["average"] is not None),
        key=lambda s: s["average"],
        default=None,
    )

    trend_labels = json.dumps([t["week"] for t in trend])
    trend_data = json.dumps([t["average"] for t in trend])

    subject_labels = json.dumps([s["subject"] for s in stats])
    subject_data = json.dumps([s["average"] for s in stats])

    return render_template(
        "dashboard.html",
        overall_avg=overall_avg,
        total_grades=len(grades),
        best_subject=best_subject,
        worst_subject=worst_subject,
        weak_count=len(weak),
        recent_grades=recent,
        stats=stats,
        trend_labels=trend_labels,
        trend_data=trend_data,
        subject_labels=subject_labels,
        subject_data=subject_data,
        threshold=threshold,
    )
