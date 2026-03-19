# ==============================================================
# __init__.py – Applikations-Factory für ScootNow
# Initialisiert Flask, Datenbank und Login-Manager
# Autor: Cristian Quarta | DBWE.TA1A.PA | 2026
# ==============================================================

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Globale Instanzen von Datenbank und Login-Manager.
# Sie werden hier erstellt, aber erst in create_app() mit der
# Flask-App verknüpft (Application Factory Pattern).
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    """
    Application Factory: Erstellt und konfiguriert die Flask-App.
    Dieses Muster ermöglicht mehrere App-Instanzen (z.B. für Tests).
    """
    app = Flask(__name__)

    # --- Konfiguration ---
    # Geheimschlüssel für Session-Signaturen und CSRF-Schutz.
    # In einer Produktionsumgebung sollte dieser Wert aus einer
    # Umgebungsvariable gelesen werden (z.B. os.environ.get).
    app.config["SECRET_KEY"] = "supersecretkey123"

    # Verbindungsstring zur PostgreSQL-Datenbank.
    # Format: postgresql://user:passwort@host/datenbankname
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://scooteruser:Scooter123!@localhost/scooterdb"

    # Deaktiviert das SQLAlchemy Event-System für Objektänderungen.
    # Reduziert Overhead – wird in diesem Projekt nicht benötigt.
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Erweiterungen initialisieren ---
    # Verknüpft SQLAlchemy mit der Flask-App.
    db.init_app(app)

    # Verknüpft den Login-Manager mit der Flask-App.
    login_manager.init_app(app)

    # Definiert die Route, zu der nicht eingeloggte Benutzer
    # weitergeleitet werden, wenn sie eine geschützte Seite aufrufen.
    login_manager.login_view = "login"

    # --- Routen registrieren ---
    # Import innerhalb der Funktion verhindert zirkuläre Imports
    # (routes.py importiert db und models, die hier definiert sind).
    from app.routes import register_routes
    register_routes(app)

    # --- Datenbank initialisieren ---
    # Erstellt alle Tabellen in PostgreSQL, sofern sie noch nicht
    # existieren. Basiert auf den Modellen in models.py.
    with app.app_context():
        from app import models
        db.create_all()

    return app
