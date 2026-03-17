from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    api_token = db.Column(db.String(255), unique=True, nullable=True)
    role = db.Column(db.String(20), nullable=False, default="rider")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rentals = db.relationship("Rental", backref="user", lazy=True)
    scooters = db.relationship("Scooter", backref="provider", lazy=True)
    payment_methods = db.relationship("PaymentMethod", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


class Scooter(db.Model):
    __tablename__ = "scooters"

    id = db.Column(db.Integer, primary_key=True)
    scooter_code = db.Column(db.String(50), unique=True, nullable=False)
    qr_code = db.Column(db.String(100), unique=True, nullable=False)
    model = db.Column(db.String(100), nullable=False)
    battery_level = db.Column(db.Integer, nullable=False, default=100)
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    price_per_minute = db.Column(db.Float, nullable=False, default=0.35)
    base_price = db.Column(db.Float, nullable=False, default=1.50)
    status = db.Column(db.String(50), nullable=False, default="available")
    provider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    rentals = db.relationship("Rental", backref="scooter", lazy=True)

    def __repr__(self):
        return f"<Scooter {self.scooter_code}>"


class Rental(db.Model):
    __tablename__ = "rentals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    scooter_id = db.Column(db.Integer, db.ForeignKey("scooters.id"), nullable=False)

    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    total_price = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="active")

    def __repr__(self):
        return f"<Rental {self.id}>"


class PaymentMethod(db.Model):
    __tablename__ = "payment_methods"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    card_holder = db.Column(db.String(120), nullable=False)
    card_number_masked = db.Column(db.String(25), nullable=False)
    expiry_month = db.Column(db.String(2), nullable=False)
    expiry_year = db.Column(db.String(4), nullable=False)
    brand = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PaymentMethod {self.id}>"
