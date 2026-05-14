import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///eklase.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    OBSCURA_CDP_ENDPOINT = os.environ.get("OBSCURA_CDP_ENDPOINT", "http://127.0.0.1:9222")
    GRADE_SYNC_INTERVAL_MINUTES = int(os.environ.get("GRADE_SYNC_INTERVAL_MINUTES", "30"))
    WEAK_GRADE_THRESHOLD = float(os.environ.get("WEAK_GRADE_THRESHOLD", "5.0"))
    FERNET_KEY = os.environ.get("FERNET_KEY", "")
