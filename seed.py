from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Scooter, PaymentMethod

app = create_app()

with app.app_context():
    if User.query.count() == 0:
        provider = User(
            username="provider1",
            email="provider1@scootnow.local",
            password_hash=generate_password_hash("Provider123!"),
            role="provider"
        )

        rider = User(
            username="rider1",
            email="rider1@scootnow.local",
            password_hash=generate_password_hash("Rider123!"),
            role="rider"
        )

        db.session.add(provider)
        db.session.add(rider)
        db.session.commit()

        scooters = [
            Scooter(
                scooter_code="SC-1001",
                qr_code="QR-SC-1001",
                model="Xiaomi Scooter 4",
                battery_level=90,
                location="Bahnhof Zürich",
                latitude=47.378177,
                longitude=8.540192,
                price_per_minute=0.35,
                base_price=1.50,
                status="available",
                provider_id=provider.id
            ),
            Scooter(
                scooter_code="SC-1002",
                qr_code="QR-SC-1002",
                model="Segway Ninebot",
                battery_level=75,
                location="Uni Bern",
                latitude=46.948090,
                longitude=7.447440,
                price_per_minute=0.35,
                base_price=1.50,
                status="available",
                provider_id=provider.id
            ),
            Scooter(
                scooter_code="SC-1003",
                qr_code="QR-SC-1003",
                model="Voi Explorer",
                battery_level=15,
                location="Basel SBB",
                latitude=47.547600,
                longitude=7.589600,
                price_per_minute=0.35,
                base_price=1.50,
                status="available",
                provider_id=provider.id
            )
        ]

        db.session.add_all(scooters)

        card = PaymentMethod(
            user_id=rider.id,
            card_holder="Max Muster",
            card_number_masked="**** **** **** 4242",
            expiry_month="12",
            expiry_year="2028",
            brand="Visa"
        )

        db.session.add(card)
        db.session.commit()

        print("Seed-Daten erstellt")
    else:
        print("Daten existieren bereits")
