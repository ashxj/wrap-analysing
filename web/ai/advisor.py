import json
import re
import urllib.parse
from datetime import datetime, timedelta, timezone

import anthropic

from extensions import db
from models import Recommendation

CACHE_TTL_DAYS = 7

# Subject name → uzdevumi.lv URL slug (Latvian and Russian names)
SUBJECT_SLUGS: dict[str, str] = {
    "matemātika": "matematika",
    "latviešu valoda": "latviesu-valoda",
    "latviešu valoda un literatūra": "latviesu-valoda",
    "literatūra": "latviesu-valoda",
    "angļu valoda": "anglu-valoda",
    "vācu valoda": "vaciesu-valoda",
    "franču valoda": "francu-valoda",
    "krievu valoda": "krievu-valoda",
    "fizika": "fizika",
    "ķīmija": "kimija",
    "bioloģija": "biologija",
    "ģeogrāfija": "geografija",
    "vēsture": "vesture",
    "informātika": "informatika",
    "datorika": "datorika",
    "programmēšana": "programmesana",
    "dabaszinības": "dabaszinibas",
    "sociālās zinātnes": "socialie-zinatnes",
    # English subject names
    "mathematics": "matematika",
    "latvian language": "latviesu-valoda",
    "english language": "anglu-valoda",
    "german language": "vaciesu-valoda",
    "russian language": "krievu-valoda",
    "physics": "fizika",
    "chemistry": "kimija",
    "biology": "biologija",
    "geography": "geografija",
    "history": "vesture",
    "computer science": "informatika",
    "natural science": "dabaszinibas",
    "social science": "socialie-zinatnes",
}

SYSTEM_PROMPT = """\
You are an educational assistant for Latvian school students. You receive a subject, class/grade, and specific lesson topics the student has studied (ordered by priority — lowest grades first).

Generate 5–7 high-quality resource links for studying these topics.

CONFIRMED WORKING URL FORMATS — use ONLY these patterns:

1. uzdevumi.lv (Latvian school platform — ALWAYS include at least one):
   Category page:  {uzdevumi_url}
   Search page:    https://www.uzdevumi.lv/search?q={{URL-encoded-topic}}
   ⚠ Never invent /p/…/re-UUID or /p/…/tv-UUID URLs — they are unpredictable.

2. skola2030.lv (official Latvian curriculum portal — theory materials and tasks):
   Search: https://skola2030.lv/lv/search?phrase={{URL-encoded-topic}}
   Always valid for any Latvian school subject.

3. maciunmacies.lv (Latvian e-learning platform):
   https://www.maciunmacies.lv/

4. letonika.lv (Latvian encyclopedia and educational reference):
   https://www.letonika.lv/search/?q={{URL-encoded-topic}}

5. Wikipedia — only if you are CERTAIN the article exists at that exact title:
   Latvian: https://lv.wikipedia.org/wiki/{{Title_With_Underscores}}
   English: https://en.wikipedia.org/wiki/{{Title_With_Underscores}}

6. GeoGebra (math / geometry / graphing):
   https://www.geogebra.org/search/{{topic-slug}}

7. PhET Interactive Simulations (physics / chemistry / biology):
   https://phet.colorado.edu/en/simulations/filter?subjects={{slug}}
   slugs: physics | chemistry | biology | math | earth-science

8. Wolfram MathWorld (math theory — English terms only):
   https://mathworld.wolfram.com/{{CamelCaseArticleName}}.html

RULES:
- "covers" must contain only topics copied exactly from the provided list
- Prefer Latvian-language resources first, English second — do NOT include Russian-language resources
- Write ALL "title" and "description" values in English only — never in Russian
- Do NOT include YouTube or Khan Academy links
- Do NOT hallucinate Wikipedia article names — when unsure, use skola2030.lv or uzdevumi.lv instead

Reply as a JSON array only, no extra text:
[
  {{
    "title": "Resource name",
    "url": "https://...",
    "description": "What this explains and why it is useful for these topics (1–2 sentences)",
    "type": "website|course",
    "language": "lv|en|ru",
    "covers": ["exact topic from list"]
  }}
]"""


def _get_uzdevumi_url(subject: str, class_name: str) -> str:
    subject_lower = subject.lower().strip()
    slug = SUBJECT_SLUGS.get(subject_lower)
    if not slug:
        for key, val in SUBJECT_SLUGS.items():
            if val and (key in subject_lower or subject_lower in key):
                slug = val
                break
    if not slug:
        return f"https://www.uzdevumi.lv/search?q={urllib.parse.quote_plus(subject)}"

    grade_match = re.search(r"\d+", class_name or "")
    grade = grade_match.group() if grade_match else None
    if grade:
        return f"https://www.uzdevumi.lv/p/{slug}/{grade}-klase/"
    return f"https://www.uzdevumi.lv/p/{slug}/"


def get_recommendations(user_id: int, subject: str, class_name: str, topics: list, api_key: str) -> list:
    cached = Recommendation.query.filter_by(user_id=user_id, subject=subject).first()
    if cached:
        age = datetime.now(timezone.utc) - cached.generated_at.replace(tzinfo=timezone.utc)
        if age < timedelta(days=CACHE_TTL_DAYS):
            return cached.content

    recs = _generate_with_claude(subject, class_name, topics, api_key)
    _save_to_cache(user_id, subject, recs, cached)
    return recs


def refresh_recommendations(user_id: int, subject: str, class_name: str, topics: list, api_key: str) -> list:
    recs = _generate_with_claude(subject, class_name, topics, api_key)
    cached = Recommendation.query.filter_by(user_id=user_id, subject=subject).first()
    _save_to_cache(user_id, subject, recs, cached)
    return recs


def _save_to_cache(user_id: int, subject: str, recs: list, cached) -> None:
    if cached:
        cached.content = recs
        cached.generated_at = datetime.now(timezone.utc)
    else:
        rec = Recommendation(user_id=user_id, subject=subject)
        rec.content = recs
        db.session.add(rec)
    db.session.commit()


def _generate_with_claude(subject: str, class_name: str, topics: list, api_key: str) -> list:
    if not api_key:
        return _fallback_recommendations(subject, class_name, topics)

    uzdevumi_url = _get_uzdevumi_url(subject, class_name)
    system_prompt = SYSTEM_PROMPT.format(uzdevumi_url=uzdevumi_url)

    if topics:
        topics_block = "\n".join(f"- {t}" for t in topics)
        user_prompt = (
            f"Subject: {subject}\n"
            f"Class: {class_name or 'unknown'}\n"
            f"Topics (lowest grades first):\n{topics_block}\n\n"
            f"Find 5–7 theory and video resources for these specific topics."
        )
    else:
        user_prompt = (
            f"Subject: {subject}\n"
            f"Class: {class_name or 'unknown'}\n"
            f"No specific topics available. Find 5 general theory resources for this subject."
        )

    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = message.content[0].text.strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            recs = json.loads(text[start:end])
            for r in recs:
                if "covers" not in r:
                    r["covers"] = []
            return recs
        return _fallback_recommendations(subject, class_name, topics)
    except Exception:
        return _fallback_recommendations(subject, class_name, topics)


def _fallback_recommendations(subject: str, class_name: str, topics: list) -> list:
    covers = topics[:2] if topics else []
    uzdevumi_url = _get_uzdevumi_url(subject, class_name)
    q_subject = urllib.parse.quote_plus(subject)
    q_topic = urllib.parse.quote_plus(f"{topics[0]} {subject}") if topics else q_subject
    return [
        {
            "title": f"uzdevumi.lv — {subject}",
            "url": uzdevumi_url,
            "description": "Latvian school exercise and theory platform — browse topics by grade level.",
            "type": "website",
            "language": "lv",
            "covers": covers,
        },
        {
            "title": f"Skola 2030 — {subject}",
            "url": f"https://skola2030.lv/lv/search?phrase={q_topic}",
            "description": "Official Latvian curriculum portal with theory materials and learning tasks.",
            "type": "website",
            "language": "lv",
            "covers": covers,
        },
        {
            "title": f"letonika.lv — {subject}",
            "url": f"https://www.letonika.lv/search/?q={q_topic}",
            "description": "Latvian encyclopaedia and educational reference for school subjects.",
            "type": "website",
            "language": "lv",
            "covers": covers,
        },
    ]
