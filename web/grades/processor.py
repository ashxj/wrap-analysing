import re
from datetime import datetime, timezone
from html.parser import HTMLParser

from extensions import db
from models import Grade


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        self._parts.append(data)

    def get_text(self):
        return " ".join(self._parts).strip()


def strip_html(text: str) -> str:
    if not text:
        return ""
    s = _HTMLStripper()
    s.feed(text)
    return s.get_text()


def _collect_evaluations(value, result: list):
    if isinstance(value, list):
        for item in value:
            _collect_evaluations(item, result)
        return
    if not isinstance(value, dict):
        return
    if isinstance(value.get("evaluations"), list):
        for ev in value["evaluations"]:
            lesson = ev.get("lesson") or {}
            lesson_type_obj = lesson.get("type") or {}
            result.append({
                "id": ev.get("id"),
                "value": ev.get("value") or ev.get("studentEvaluation"),
                "subject": (
                    lesson.get("lessonSubject", {}).get("name")
                    or ev.get("lessonSubject", {}).get("name")
                    or ev.get("disciplineName")
                    or value.get("disciplineName")
                    or value.get("name")
                ),
                "date": lesson.get("date") or lesson.get("lessonDate") or ev.get("lessonDate"),
                "lesson_type": lesson_type_obj.get("name"),
                "lesson_type_abbr": lesson_type_obj.get("abbreviation"),
                "lesson_topic": strip_html(lesson.get("subject", "")),
                "is_test": lesson.get("isTest", False),
                "time_created": ev.get("timeCreated"),
                "raw": ev,
            })
    for nested in value.values():
        _collect_evaluations(nested, result)


def normalize_evaluations(summary: dict) -> list:
    result = []
    _collect_evaluations(summary, result)
    seen = set()
    deduped = []
    for g in result:
        key = str(g["id"]) if g["id"] is not None else str(g["raw"])
        if key not in seen:
            seen.add(key)
            deduped.append(g)
    return deduped


def _parse_numeric(value) -> float | None:
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


def _grade_sort_ts(g: dict) -> float:
    for key in ("time_created", "date"):
        val = g.get(key)
        if val:
            try:
                dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                return dt.timestamp()
            except Exception:
                pass
    return 0.0


def compute_subject_stats(grades: list) -> list:
    by_subject: dict = {}
    for g in grades:
        subj = g.get("subject") or "Unknown Subject"
        if subj not in by_subject:
            by_subject[subj] = {"subject": subj, "numeric": [], "all_values": [], "latest": None, "grades": []}
        stat = by_subject[subj]
        stat["all_values"].append(g.get("value"))
        stat["grades"].append(g)
        ts = _grade_sort_ts(g)
        if stat["latest"] is None or ts > _grade_sort_ts(stat["latest"]):
            stat["latest"] = g
        num = _parse_numeric(g.get("value"))
        if num is not None:
            stat["numeric"].append(num)

    result = []
    for stat in by_subject.values():
        nums = stat["numeric"]
        average = round(sum(nums) / len(nums), 2) if nums else None
        result.append({
            "subject": stat["subject"],
            "average": average,
            "numeric_count": len(nums),
            "total_count": len(stat["all_values"]),
            "latest": stat["latest"],
            "values": stat["all_values"],
            "grades": stat["grades"],
        })

    result.sort(key=lambda x: x["subject"])
    return result


def find_weak_subjects(stats: list, threshold: float = 5.0) -> list:
    return [s for s in stats if s["average"] is not None and s["average"] < threshold]


def find_weak_lesson_types(grades: list, subject: str) -> list:
    subject_grades = [g for g in grades if (g.get("subject") or "") == subject]
    by_type: dict = {}
    for g in subject_grades:
        lt = g.get("lesson_type") or "Unknown"
        if lt not in by_type:
            by_type[lt] = []
        num = _parse_numeric(g.get("value"))
        if num is not None:
            by_type[lt].append(num)

    result = []
    for lt, vals in by_type.items():
        if vals:
            avg = round(sum(vals) / len(vals), 2)
            result.append({"lesson_type": lt, "average": avg, "count": len(vals)})
    result.sort(key=lambda x: x["average"])
    return result


def sort_grades_by_date(grades: list) -> list:
    return sorted(grades, key=_grade_sort_ts, reverse=True)


def weekly_average_trend(grades: list) -> list:
    from collections import defaultdict
    weeks: dict = defaultdict(list)
    for g in grades:
        num = _parse_numeric(g.get("value"))
        if num is None:
            continue
        ts = _grade_sort_ts(g)
        if ts == 0:
            continue
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        week_key = dt.strftime("%Y-W%W")
        weeks[week_key].append(num)

    trend = []
    for week in sorted(weeks.keys()):
        vals = weeks[week]
        trend.append({"week": week, "average": round(sum(vals) / len(vals), 2), "count": len(vals)})
    return trend


def save_grades_to_db(user_id: int, normalized_grades: list):
    for g in normalized_grades:
        api_id = g.get("id")
        if api_id is not None:
            existing = Grade.query.filter_by(user_id=user_id, grade_api_id=api_id).first()
            if existing:
                continue

        def _parse_dt(val):
            if not val:
                return None
            try:
                return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except Exception:
                return None

        grade = Grade(
            user_id=user_id,
            grade_api_id=api_id,
            value=str(g.get("value")) if g.get("value") is not None else None,
            subject=g.get("subject"),
            lesson_date=_parse_dt(g.get("date")),
            created_at=_parse_dt(g.get("time_created")),
            lesson_type=g.get("lesson_type"),
            lesson_type_abbr=g.get("lesson_type_abbr"),
            lesson_topic=g.get("lesson_topic"),
            is_test=bool(g.get("is_test", False)),
        )
        grade.raw = g.get("raw", {})
        db.session.add(grade)

    db.session.commit()


def grades_to_dicts(db_grades: list) -> list:
    result = []
    for g in db_grades:
        result.append({
            "id": g.grade_api_id,
            "value": g.value,
            "subject": g.subject,
            "date": g.lesson_date.isoformat() if g.lesson_date else None,
            "time_created": g.created_at.isoformat() if g.created_at else None,
            "lesson_type": g.lesson_type,
            "lesson_type_abbr": g.lesson_type_abbr,
            "lesson_topic": g.lesson_topic,
            "is_test": g.is_test,
            "raw": g.raw,
        })
    return result
