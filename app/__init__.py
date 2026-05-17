from datetime import datetime, timezone

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from config import Config


db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "main.login"


def _timeago(dt):
    """Render a datetime as 'just now' / '5 min ago' / 'yesterday' / etc."""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    seconds = int((datetime.now(timezone.utc) - dt).total_seconds())
    if seconds < 45:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    weeks = days // 7
    if weeks < 5:
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    months = days // 30
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''} ago"
    years = days // 365
    return f"{years} year{'s' if years != 1 else ''} ago"


def _is_emoji_like(s):
    """Used as a Jinja test (`{% if x is emoji %}`).

    True only when the string looks like an emoji — no ASCII letters,
    digits or whitespace. Used to hide legacy text that ended up
    in the `cover_emoji` field before the picker was tightened.
    """
    if not s:
        return False
    return not any(ch.isascii() and (ch.isalnum() or ch.isspace()) for ch in str(s))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    app.jinja_env.filters["timeago"] = _timeago
    app.jinja_env.tests["emoji"] = _is_emoji_like

    from app import models
    from app.routes import main
    app.register_blueprint(main)

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Initialized the database.")

    return app
