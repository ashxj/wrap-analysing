from flask import Flask

from config import Config
from extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from auth.routes import auth_bp
    from grades.routes import grades_bp
    from ai.routes import ai_bp
    from dashboard.routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(grades_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(dashboard_bp)

    with app.app_context():
        db.create_all()

    _start_scheduler(app)

    return app


def _start_scheduler(app: Flask):
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        interval = app.config["GRADE_SYNC_INTERVAL_MINUTES"]

        def scheduled_sync():
            with app.app_context():
                _sync_all_users(app)

        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(scheduled_sync, "interval", minutes=interval)
        scheduler.start()
    except Exception as e:
        app.logger.warning(f"Scheduler not started: {e}")


def _sync_all_users(app):
    from models import User
    from auth.oidc import token_expired, fetch_grades_sync, login_to_eklase
    from auth.routes import decrypt_password
    from grades.processor import save_grades_to_db
    from datetime import datetime, timezone
    import asyncio

    users = User.query.all()
    for user in users:
        try:
            expires_at_ms = user.token_expires_at.timestamp() * 1000 if user.token_expires_at else None
            if token_expired(expires_at_ms):
                password = decrypt_password(user.eklase_password_encrypted)
                cdp = app.config["OBSCURA_CDP_ENDPOINT"]
                result = asyncio.run(login_to_eklase(user.eklase_username, password, user.profile_id, cdp))
                tokens = result["tokens"]
                user.access_token = tokens["access_token"]
                user.token_expires_at = datetime.fromtimestamp(tokens["expires_at"] / 1000, tz=timezone.utc)
                from extensions import db
                db.session.commit()

            data = fetch_grades_sync(user.access_token)
            save_grades_to_db(user.id, data["grades"])
            user.last_synced_at = datetime.now(timezone.utc)
            from extensions import db
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Scheduled sync failed for user {user.id}: {e}")
