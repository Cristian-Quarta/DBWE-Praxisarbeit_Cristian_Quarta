from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "supersecretkey123"
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://scooteruser:Scooter123!@localhost/scooterdb"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    from app.routes import register_routes
    register_routes(app)

    with app.app_context():
        from app import models
        db.create_all()

    return app
