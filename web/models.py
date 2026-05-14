import json
from datetime import datetime, timezone
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    eklase_username = db.Column(db.String(255), unique=True, nullable=False)
    eklase_password_encrypted = db.Column(db.Text, nullable=False)
    profile_id = db.Column(db.String(64), default="")
    profile_json = db.Column(db.Text, default="{}")
    access_token = db.Column(db.Text, default="")
    token_expires_at = db.Column(db.DateTime, nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    grades = db.relationship("Grade", backref="user", lazy=True, cascade="all, delete-orphan")
    recommendations = db.relationship("Recommendation", backref="user", lazy=True, cascade="all, delete-orphan")

    @property
    def profile(self):
        try:
            return json.loads(self.profile_json or "{}")
        except Exception:
            return {}

    @profile.setter
    def profile(self, value):
        self.profile_json = json.dumps(value, ensure_ascii=False)

    @property
    def display_name(self):
        p = self.profile
        first = p.get("firstName", "")
        last = p.get("lastName", "")
        name = f"{first} {last}".strip()
        return name or self.eklase_username

    @property
    def class_name(self):
        return self.profile.get("className", "")

    @property
    def school_name(self):
        return self.profile.get("schoolName", "")


class Grade(db.Model):
    __tablename__ = "grades"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    grade_api_id = db.Column(db.BigInteger, nullable=True)
    value = db.Column(db.String(32), nullable=True)
    subject = db.Column(db.String(255), nullable=True)
    lesson_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)
    lesson_type = db.Column(db.String(128), nullable=True)
    lesson_type_abbr = db.Column(db.String(32), nullable=True)
    lesson_topic = db.Column(db.Text, nullable=True)
    is_test = db.Column(db.Boolean, default=False)
    raw_json = db.Column(db.Text, default="{}")

    __table_args__ = (
        db.UniqueConstraint("user_id", "grade_api_id", name="uq_user_grade"),
    )

    @property
    def raw(self):
        try:
            return json.loads(self.raw_json or "{}")
        except Exception:
            return {}

    @raw.setter
    def raw(self, value):
        self.raw_json = json.dumps(value, ensure_ascii=False)

    def numeric_value(self):
        if self.value is None:
            return None
        text = str(self.value).strip().replace(",", ".")
        import re
        if not re.match(r"^\d+(\.\d+)?$", text):
            return None
        try:
            v = float(text)
            return v if 1 <= v <= 10 else None
        except ValueError:
            return None


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    content_json = db.Column(db.Text, default="[]")
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def content(self):
        try:
            return json.loads(self.content_json or "[]")
        except Exception:
            return []

    @content.setter
    def content(self, value):
        self.content_json = json.dumps(value, ensure_ascii=False)
