# ==============================================================
# models.py – Datenbankmodelle für ScootNow
# Definiert alle Tabellen via SQLAlchemy ORM:
# User, Scooter, Rental, PaymentMethod
# Autor: Cristian Quarta | DBWE.TA1A.PA | 2026
# ==============================================================

from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


# --- User Loader ---
# Flask-Login benötigt diese Funktion, um einen eingeloggten
# Benutzer anhand seiner ID aus der Datenbank zu laden.
# Wird bei jeder geschützten Anfrage automatisch aufgerufen.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==============================================================
# Modell: User
# Speichert alle Benutzer der Applikation – sowohl Rider als
# auch Provider. Die Rolle wird über das Attribut "role" gesteuert.
# ==============================================================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    # Primärschlüssel – eindeutige Benutzer-ID
    id = db.Column(db.Integer, primary_key=True)

    # Benutzername – eindeutig, max. 80 Zeichen
    username = db.Column(db.String(80), unique=True, nullable=False)

    # E-Mail-Adresse – eindeutig, max. 120 Zeichen
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Passwort-Hash – wird nie im Klartext gespeichert.
    # Hashing erfolgt mit werkzeug.security (PBKDF2-SHA256).
    password_hash = db.Column(db.String(255), nullable=False)

    # API-Token für die tokenbasierte Authentifizierung der REST-API.
    # Wird bei /api/login generiert und ist optional (nullable).
    api_token = db.Column(db.String(255), unique=True, nullable=True)

    # Benutzerrolle: "rider" (Standard) oder "provider".
    # Steuert den gesamten rollenbasierten Zugriff der Applikation.
    role = db.Column(db.String(20), nullable=False, default="rider")

    # Erstellungszeitpunkt des Benutzerkontos (UTC)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Beziehungen (1:n) ---
    # Ein User (Rider) kann mehrere Fahrten (Rentals) haben.
    rentals = db.relationship("Rental", backref="user", lazy=True)

    # Ein User (Provider) kann mehrere Scooter verwalten.
    scooters = db.relationship("Scooter", backref="provider", lazy=True)

    # Ein User (Rider) kann mehrere Zahlungsmittel hinterlegen.
    payment_methods = db.relationship("PaymentMethod", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


# ==============================================================
# Modell: Scooter
# Repräsentiert einen E-Scooter in der Flotte eines Providers.
# Enthält Standort, Akkustand, Preisinformationen und Status.
# ==============================================================
class Scooter(db.Model):
    __tablename__ = "scooters"

    # Primärschlüssel – eindeutige Scooter-ID
    id = db.Column(db.Integer, primary_key=True)

    # Eindeutiger Scooter-Code (z.B. "SC-1001")
    scooter_code = db.Column(db.String(50), unique=True, nullable=False)

    # QR-Code zur Entsperrung des Scooters durch den Rider.
    # Muss mit der Benutzereingabe übereinstimmen, um die Fahrt zu starten.
    qr_code = db.Column(db.String(100), unique=True, nullable=False)

    # Modellbezeichnung des Scooters (z.B. "Xiaomi Scooter 4")
    model = db.Column(db.String(100), nullable=False)

    # Akkustand in Prozent (0–100). Scooter mit < 20% können nicht gemietet werden.
    battery_level = db.Column(db.Integer, nullable=False, default=100)

    # Textuelle Standortbeschreibung (z.B. "Bahnhof Zürich")
    location = db.Column(db.String(255), nullable=False)

    # GPS-Koordinaten – optional, für spätere Kartendarstellung verwendbar
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    # Preis pro Minute in CHF (Standard: 0.35)
    price_per_minute = db.Column(db.Float, nullable=False, default=0.35)

    # Grundpreis pro Mietvorgang in CHF (Standard: 1.50)
    base_price = db.Column(db.Float, nullable=False, default=1.50)

    # Status des Scooters: "available" (verfügbar) oder "rented" (vermietet)
    status = db.Column(db.String(50), nullable=False, default="available")

    # Fremdschlüssel – verknüpft den Scooter mit dem zuständigen Provider.
    # nullable=True erlaubt Scooter ohne zugewiesenen Provider.
    provider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Ein Scooter kann mehrere abgeschlossene Fahrten (Rentals) haben.
    rentals = db.relationship("Rental", backref="scooter", lazy=True)

    def __repr__(self):
        return f"<Scooter {self.scooter_code}>"


# ==============================================================
# Modell: Rental
# Verbindet einen Rider mit einem Scooter für eine Mietperiode.
# Speichert Start-/Endzeit, Dauer und berechneten Gesamtpreis.
# ==============================================================
class Rental(db.Model):
    __tablename__ = "rentals"

    # Primärschlüssel – eindeutige Miet-ID
    id = db.Column(db.Integer, primary_key=True)

    # Fremdschlüssel – verknüpft die Miete mit dem Rider
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Fremdschlüssel – verknüpft die Miete mit dem gemieteten Scooter
    scooter_id = db.Column(db.Integer, db.ForeignKey("scooters.id"), nullable=False)

    # Startzeitpunkt der Fahrt (UTC), wird automatisch gesetzt
    start_time = db.Column(db.DateTime, default=datetime.utcnow)

    # Endzeitpunkt der Fahrt – bleibt leer (nullable) bis die Fahrt beendet wird
    end_time = db.Column(db.DateTime, nullable=True)

    # Fahrtdauer in Minuten – wird bei Fahrtende berechnet (min. 1 Minute)
    duration_minutes = db.Column(db.Integer, nullable=True)

    # Gesamtpreis in CHF – wird bei Fahrtende berechnet:
    # total_price = base_price + (duration_minutes * price_per_minute)
    total_price = db.Column(db.Float, nullable=True)

    # Status der Miete: "active" (laufend) oder "completed" (abgeschlossen)
    status = db.Column(db.String(50), nullable=False, default="active")

    def __repr__(self):
        return f"<Rental {self.id}>"


# ==============================================================
# Modell: PaymentMethod
# Speichert Zahlungsmittel eines Riders in maskierter Form.
# Kreditkartennummern werden nie vollständig gespeichert.
# ==============================================================
class PaymentMethod(db.Model):
    __tablename__ = "payment_methods"

    # Primärschlüssel – eindeutige Zahlungsmittel-ID
    id = db.Column(db.Integer, primary_key=True)

    # Fremdschlüssel – verknüpft das Zahlungsmittel mit dem Rider
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Name des Karteninhabers
    card_holder = db.Column(db.String(120), nullable=False)

    # Maskierte Kartennummer – nur die letzten 4 Ziffern werden gespeichert.
    # Format: "**** **** **** 4242"
    card_number_masked = db.Column(db.String(25), nullable=False)

    # Ablaufmonat der Karte (z.B. "12")
    expiry_month = db.Column(db.String(2), nullable=False)

    # Ablaufjahr der Karte (z.B. "2028")
    expiry_year = db.Column(db.String(4), nullable=False)

    # Kartenmarke (z.B. "Visa", "Mastercard") – optional
    brand = db.Column(db.String(30), nullable=True)

    # Erstellungszeitpunkt des Zahlungsmittels (UTC)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PaymentMethod {self.id}>"
