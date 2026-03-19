# ==============================================================
# seed.py – Initialdaten für ScootNow
# Befüllt die Datenbank mit Testdaten für Entwicklung und Demo.
# Wird einmalig manuell ausgeführt: python seed.py
# ACHTUNG: Nur ausführen wenn die Datenbank leer ist.
# Autor: Cristian Quarta | DBWE.TA1A.PA | 2026
# ==============================================================

from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Scooter, PaymentMethod

# Flask-App initialisieren – benötigt für Datenbankzugriff
app = create_app()

with app.app_context():

    # Prüft ob bereits Benutzer in der Datenbank existieren.
    # Verhindert doppelte Seed-Daten bei mehrfacher Ausführung.
    if User.query.count() == 0:

        # ------------------------------------------------------
        # Testbenutzer erstellen
        # Passwörter werden gehasht gespeichert (PBKDF2-SHA256)
        # ------------------------------------------------------

        # Provider-Account: verwaltet die Scooter-Flotte
        provider = User(
            username="provider1",
            email="provider1@scootnow.local",
            password_hash=generate_password_hash("Provider123!"),
            role="provider"
        )

        # Rider-Account: kann Scooter mieten und Fahrten abrechnen
        rider = User(
            username="rider1",
            email="rider1@scootnow.local",
            password_hash=generate_password_hash("Rider123!"),
            role="rider"
        )

        db.session.add(provider)
        db.session.add(rider)

        # Commit nötig damit provider.id verfügbar ist für Scooter-Zuweisung
        db.session.commit()

        # ------------------------------------------------------
        # Testscooter erstellen
        # Drei Scooter an verschiedenen Standorten in der Schweiz.
        # SC-1003 hat Akkustand < 20% und kann nicht gemietet werden
        # (dient als Testfall für die Akkustand-Validierung).
        # ------------------------------------------------------
        scooters = [
            Scooter(
                scooter_code="SC-1001",
                qr_code="QR-SC-1001",        # QR-Code zum Entsperren
                model="Xiaomi Scooter 4",
                battery_level=90,             # Voll aufgeladen – mietbar
                location="Bahnhof Zürich",
                latitude=47.378177,           # GPS-Koordinaten Zürich HB
                longitude=8.540192,
                price_per_minute=0.35,        # CHF 0.35 pro Minute
                base_price=1.50,              # CHF 1.50 Grundpreis
                status="available",
                provider_id=provider.id       # Zugewiesen an provider1
            ),
            Scooter(
                scooter_code="SC-1002",
                qr_code="QR-SC-1002",
                model="Segway Ninebot",
                battery_level=75,             # Gut aufgeladen – mietbar
                location="Uni Bern",
                latitude=46.948090,           # GPS-Koordinaten Uni Bern
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
                battery_level=15,             # Akkustand < 20% – NICHT mietbar
                location="Basel SBB",         # Testfall: Akkustand-Validierung
                latitude=47.547600,           # GPS-Koordinaten Basel SBB
                longitude=7.589600,
                price_per_minute=0.35,
                base_price=1.50,
                status="available",
                provider_id=provider.id
            )
        ]

        # Alle drei Scooter in einer Operation zur Session hinzufügen
        db.session.add_all(scooters)

        # ------------------------------------------------------
        # Testzahlungsmittel für rider1 erstellen
        # Kartennummer wird nur maskiert gespeichert.
        # Ermöglicht dem Rider sofort eine Fahrt zu starten.
        # ------------------------------------------------------
        card = PaymentMethod(
            user_id=rider.id,
            card_holder="Max Muster",
            card_number_masked="**** **** **** 4242",  # Nur letzte 4 Ziffern
            expiry_month="12",
            expiry_year="2028",
            brand="Visa"
        )

        db.session.add(card)

        # Alle Scooter und Zahlungsmittel in einem Commit speichern
        db.session.commit()

        print("Seed-Daten erfolgreich erstellt:")
        print("  - Benutzer: provider1 / Provider123!")
        print("  - Benutzer: rider1 / Rider123!")
        print("  - Scooter: SC-1001 (Zürich), SC-1002 (Bern), SC-1003 (Basel)")
        print("  - Zahlungsmittel: Visa **** 4242 für rider1")

    else:
        # Datenbank enthält bereits Daten – kein Seed nötig
        print("Daten existieren bereits – Seed wird übersprungen.")
