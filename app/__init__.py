import os

from dotenv import load_dotenv
from flask import Flask, session

from app.extensions import db


def create_app(config_object: str | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "app.db")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.sets import sets_bp
    from app.blueprints.search import search_bp
    from app.blueprints.profile import profile_bp
    from app.blueprints.analytics import analytics_bp
    from app.blueprints.settings import settings_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(sets_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_user():
        from app.models import User

        uid = session.get("user_id")
        u = User.query.get(uid) if uid else None
        return dict(current_user=u)

    @app.errorhandler(404)
    def not_found(_e):
        from flask import render_template

        return render_template("errors/404.html"), 404

    return app
