from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Outside of main package
    from app.main.models import User, StudySet, Flashcard
    
    #blueprint for dahsboard
    from app.main.routes import main
    app.register_blueprint(main)

    from app.auth.routes import auth
    app.register_blueprint(auth)

    return app
