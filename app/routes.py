# ==============================================================
# routes.py – Routen und Geschäftslogik für ScootNow
# Enthält alle Web-Routen (Browser) und API-Endpunkte (REST)
# Autor: Cristian Quarta | DBWE.TA1A.PA | 2026
# ==============================================================

from datetime import datetime
import secrets

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User, Scooter, Rental, PaymentMethod


# ==============================================================
# Hilfsfunktion: API-Benutzer via Bearer Token authentifizieren
# Liest den Authorization-Header aus und gibt den zugehörigen
# User zurück – oder None, wenn kein gültiger Token vorhanden ist.
# ==============================================================
def get_api_user():
    auth_header = request.headers.get("Authorization")

    # Prüft ob Header vorhanden und korrekt formatiert ist
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    # Extrahiert den Token nach "Bearer "
    token = auth_header.split(" ", 1)[1]

    # Sucht den Benutzer anhand des Tokens in der Datenbank
    return User.query.filter_by(api_token=token).first()


# ==============================================================
# Routen-Registrierung
# Alle Routen werden als innere Funktionen registriert, um
# zirkuläre Imports mit models.py und __init__.py zu vermeiden.
# ==============================================================
def register_routes(app):

    # ----------------------------------------------------------
    # Route: Startseite
    # Zeigt alle verfügbaren Scooter auf der Übersichtsseite an.
    # Öffentlich zugänglich – kein Login erforderlich.
    # ----------------------------------------------------------
    @app.route("/")
    def home():
        scooters = Scooter.query.all()
        return render_template("home.html", scooters=scooters)


    # ----------------------------------------------------------
    # Route: Registrierung
    # GET:  Zeigt das Registrierungsformular an.
    # POST: Verarbeitet die Formulardaten und legt einen neuen
    #       Benutzer an. Passwort wird gehasht gespeichert.
    #       Doppelte Benutzernamen oder E-Mails werden abgewiesen.
    # ----------------------------------------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            role = request.form.get("role")

            # Prüft ob Benutzername oder E-Mail bereits existieren
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing_user:
                flash("Benutzername oder E-Mail existiert bereits.")
                return redirect(url_for("register"))

            # Standardrolle ist "rider", falls keine Rolle gewählt wurde
            if not role:
                role = "rider"

            # Neuen Benutzer erstellen – Passwort wird nie im Klartext gespeichert
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role
            )

            db.session.add(user)
            db.session.commit()

            flash("Registrierung erfolgreich. Bitte einloggen.")
            return redirect(url_for("login"))

        return render_template("register.html")


    # ----------------------------------------------------------
    # Route: Login
    # GET:  Zeigt das Login-Formular an.
    # POST: Prüft Benutzername und Passwort-Hash. Bei Erfolg
    #       wird die Session via flask_login gestartet.
    # ----------------------------------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            user = User.query.filter_by(username=username).first()

            # Passwort-Hash wird mit werkzeug.security verglichen
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash("Login erfolgreich.")
                return redirect(url_for("dashboard"))

            flash("Ungültiger Benutzername oder Passwort.")
            return redirect(url_for("login"))

        return render_template("login.html")


    # ----------------------------------------------------------
    # Route: Dashboard
    # Rollenbasierte Weiterleitung:
    # - Provider sieht seine eigene Scooter-Flotte
    # - Rider sieht Fahrhistorie, verfügbare Scooter und aktive Miete
    # Nur für eingeloggte Benutzer zugänglich (@login_required)
    # ----------------------------------------------------------
    @app.route("/dashboard")
    @login_required
    def dashboard():
        # Provider-Dashboard: nur eigene Scooter anzeigen
        if current_user.role == "provider":
            scooters = Scooter.query.filter_by(provider_id=current_user.id).all()
            return render_template("provider_dashboard.html", scooters=scooters)

        # Rider-Dashboard: Fahrhistorie, alle Scooter, aktive Miete und Zahlungsmittel
        rentals = Rental.query.filter_by(user_id=current_user.id).order_by(Rental.id.desc()).all()
        scooters = Scooter.query.all()
        active_rental = Rental.query.filter_by(user_id=current_user.id, status="active").first()
        payment_methods_list = PaymentMethod.query.filter_by(user_id=current_user.id).all()

        return render_template(
            "dashboard.html",
            rentals=rentals,
            scooters=scooters,
            active_rental=active_rental,
            payment_methods_list=payment_methods_list
        )


    # ----------------------------------------------------------
    # Route: Zahlungsmittel verwalten
    # GET:  Zeigt alle hinterlegten Zahlungsmittel des Riders.
    # POST: Speichert ein neues Zahlungsmittel. Die Kartennummer
    #       wird maskiert gespeichert (nur letzte 4 Ziffern).
    # Nur für Rider zugänglich.
    # ----------------------------------------------------------
    @app.route("/payment-methods", methods=["GET", "POST"])
    @login_required
    def payment_methods():
        # Rollenprüfung – nur Rider dürfen Zahlungsmittel verwalten
        if current_user.role != "rider":
            flash("Nur Fahrer können Zahlungsmittel verwalten.")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            card_holder = request.form.get("card_holder")
            card_number = request.form.get("card_number")
            expiry_month = request.form.get("expiry_month")
            expiry_year = request.form.get("expiry_year")
            brand = request.form.get("brand")

            # Pflichtfeldvalidierung
            if not card_holder or not card_number or not expiry_month or not expiry_year:
                flash("Bitte alle Pflichtfelder für das Zahlungsmittel ausfüllen.")
                return redirect(url_for("payment_methods"))

            # Kartennummer maskieren – nur letzte 4 Ziffern werden gespeichert
            masked = "**** **** **** " + card_number[-4:]

            payment = PaymentMethod(
                user_id=current_user.id,
                card_holder=card_holder,
                card_number_masked=masked,
                expiry_month=expiry_month,
                expiry_year=expiry_year,
                brand=brand
            )

            db.session.add(payment)
            db.session.commit()

            flash("Zahlungsmittel erfolgreich gespeichert.")
            return redirect(url_for("payment_methods"))

        methods = PaymentMethod.query.filter_by(user_id=current_user.id).all()
        return render_template("payment_methods.html", methods=methods)


    # ----------------------------------------------------------
    # Route: Scooter hinzufügen (Provider)
    # GET:  Zeigt das Erfassungsformular für einen neuen Scooter.
    # POST: Erstellt einen neuen Scooter und weist ihn dem
    #       eingeloggten Provider zu. GPS-Koordinaten und Preise
    #       sind optional mit Standardwerten belegt.
    # Nur für Provider zugänglich.
    # ----------------------------------------------------------
    @app.route("/provider/scooters/add", methods=["GET", "POST"])
    @login_required
    def add_scooter():
        if current_user.role != "provider":
            flash("Nur Anbieter dürfen Scooter verwalten.")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            scooter_code = request.form.get("scooter_code")
            qr_code = request.form.get("qr_code")
            model = request.form.get("model")
            battery_level = request.form.get("battery_level")
            location = request.form.get("location")
            latitude = request.form.get("latitude")
            longitude = request.form.get("longitude")
            price_per_minute = request.form.get("price_per_minute")
            base_price = request.form.get("base_price")
            status = request.form.get("status")

            # Pflichtfeldvalidierung
            if not scooter_code or not qr_code or not model or not battery_level or not location:
                flash("Bitte alle Pflichtfelder für den Scooter ausfüllen.")
                return redirect(url_for("add_scooter"))

            scooter = Scooter(
                scooter_code=scooter_code,
                qr_code=qr_code,
                model=model,
                battery_level=int(battery_level),
                location=location,
                # GPS-Koordinaten sind optional
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                # Standardwerte falls keine Preise angegeben
                price_per_minute=float(price_per_minute) if price_per_minute else 0.35,
                base_price=float(base_price) if base_price else 1.50,
                status=status if status else "available",
                # Scooter wird dem eingeloggten Provider zugewiesen
                provider_id=current_user.id
            )

            db.session.add(scooter)
            db.session.commit()

            flash("Scooter erfolgreich hinzugefügt.")
            return redirect(url_for("dashboard"))

        return render_template("add_scooter.html")


    # ----------------------------------------------------------
    # Route: Scooter bearbeiten (Provider)
    # GET:  Zeigt das Bearbeitungsformular mit aktuellen Werten.
    # POST: Aktualisiert die Scooter-Daten in der Datenbank.
    #       Nur der zuständige Provider darf seinen Scooter bearbeiten.
    # ----------------------------------------------------------
    @app.route("/provider/scooters/edit/<int:scooter_id>", methods=["GET", "POST"])
    @login_required
    def edit_scooter(scooter_id):
        if current_user.role != "provider":
            flash("Nur Anbieter dürfen Scooter verwalten.")
            return redirect(url_for("dashboard"))

        # Scooter laden – 404 falls nicht gefunden
        scooter = Scooter.query.get_or_404(scooter_id)

        # Sicherstellen dass der Scooter dem eingeloggten Provider gehört
        if scooter.provider_id != current_user.id:
            flash("Keine Berechtigung.")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            model = request.form.get("model")
            battery_level = request.form.get("battery_level")
            location = request.form.get("location")
            latitude = request.form.get("latitude")
            longitude = request.form.get("longitude")
            price_per_minute = request.form.get("price_per_minute")
            base_price = request.form.get("base_price")
            status = request.form.get("status")

            # Nur Felder aktualisieren, die im Formular ausgefüllt wurden
            scooter.model = model or scooter.model
            scooter.location = location or scooter.location
            scooter.status = status or scooter.status

            if battery_level:
                scooter.battery_level = int(battery_level)

            scooter.latitude = float(latitude) if latitude else None
            scooter.longitude = float(longitude) if longitude else None

            if price_per_minute:
                scooter.price_per_minute = float(price_per_minute)

            if base_price:
                scooter.base_price = float(base_price)

            db.session.commit()

            flash("Scooter erfolgreich aktualisiert.")
            return redirect(url_for("dashboard"))

        return render_template("edit_scooter.html", scooter=scooter)


    # ----------------------------------------------------------
    # Route: Scooter löschen (Provider)
    # POST: Löscht einen Scooter aus der Datenbank.
    #       Nur der zuständige Provider darf seinen Scooter löschen.
    # ----------------------------------------------------------
    @app.route("/provider/scooters/delete/<int:scooter_id>", methods=["POST"])
    @login_required
    def delete_scooter(scooter_id):
        if current_user.role != "provider":
            flash("Nur Anbieter dürfen Scooter verwalten.")
            return redirect(url_for("dashboard"))

        scooter = Scooter.query.get_or_404(scooter_id)

        # Sicherstellen dass der Scooter dem eingeloggten Provider gehört
        if scooter.provider_id != current_user.id:
            flash("Keine Berechtigung.")
            return redirect(url_for("dashboard"))

        db.session.delete(scooter)
        db.session.commit()

        flash("Scooter gelöscht.")
        return redirect(url_for("dashboard"))


    # ----------------------------------------------------------
    # Route: Scooter mieten (Rider)
    # POST: Startet eine neue Miete nach mehreren Validierungen:
    #       1. Rider hat kein aktives Zahlungsmittel → Abbruch
    #       2. Rider hat bereits eine aktive Miete → Abbruch
    #       3. Scooter ist nicht verfügbar → Abbruch
    #       4. Akkustand < 20% → Abbruch
    #       5. QR-Code stimmt nicht überein → Abbruch
    #       Bei Erfolg: Rental anlegen, Scooter auf "rented" setzen.
    # ----------------------------------------------------------
    @app.route("/rent/<int:scooter_id>", methods=["POST"])
    @login_required
    def rent_scooter(scooter_id):
        if current_user.role != "rider":
            flash("Nur Fahrer dürfen Scooter mieten.")
            return redirect(url_for("dashboard"))

        scooter = Scooter.query.get_or_404(scooter_id)
        qr_code_input = request.form.get("qr_code_input")

        # Validierung 1: Zahlungsmittel vorhanden?
        payment_method = PaymentMethod.query.filter_by(user_id=current_user.id).first()
        if not payment_method:
            flash("Vor dem Mieten muss mindestens ein Zahlungsmittel hinterlegt werden.")
            return redirect(url_for("payment_methods"))

        # Validierung 2: Bereits eine aktive Miete vorhanden?
        active_rental = Rental.query.filter_by(user_id=current_user.id, status="active").first()
        if active_rental:
            flash("Es ist bereits eine aktive Miete vorhanden.")
            return redirect(url_for("dashboard"))

        # Validierung 3: Scooter verfügbar?
        if scooter.status != "available":
            flash("Dieser Scooter ist aktuell nicht verfügbar.")
            return redirect(url_for("dashboard"))

        # Validierung 4: Akkustand mindestens 20%?
        if scooter.battery_level < 20:
            flash("Dieser Scooter kann wegen niedrigem Akkustand nicht gemietet werden.")
            return redirect(url_for("dashboard"))

        # Validierung 5: QR-Code korrekt?
        if qr_code_input != scooter.qr_code:
            flash("QR-Code ungültig. Der Scooter konnte nicht entsperrt werden.")
            return redirect(url_for("dashboard"))

        # Neue Miete erstellen und Scooter-Status aktualisieren
        rental = Rental(
            user_id=current_user.id,
            scooter_id=scooter.id,
            start_time=datetime.utcnow(),
            status="active"
        )

        # Scooter als vermietet markieren
        scooter.status = "rented"

        db.session.add(rental)
        db.session.commit()

        flash("Scooter erfolgreich gemietet und per QR-Code entsperrt.")
        return redirect(url_for("dashboard"))


    # ----------------------------------------------------------
    # Route: Fahrt beenden (Rider)
    # POST: Beendet eine aktive Miete und berechnet den Preis.
    #       Formel: total_price = base_price + (duration_min * price_per_min)
    #       Mindestdauer: 1 Minute (auch bei kürzeren Fahrten)
    #       Scooter-Status wird zurück auf "available" gesetzt.
    # ----------------------------------------------------------
    @app.route("/end_rental/<int:rental_id>", methods=["POST"])
    @login_required
    def end_rental(rental_id):
        rental = Rental.query.get_or_404(rental_id)

        # Sicherstellen dass die Miete dem eingeloggten Rider gehört
        if rental.user_id != current_user.id:
            flash("Keine Berechtigung für diese Miete.")
            return redirect(url_for("dashboard"))

        # Prüfen ob die Miete noch aktiv ist
        if rental.status != "active":
            flash("Diese Miete ist nicht mehr aktiv.")
            return redirect(url_for("dashboard"))

        # Endzeitpunkt setzen (UTC)
        rental.end_time = datetime.utcnow()

        # Fahrtdauer berechnen – mindestens 1 Minute
        duration_seconds = (rental.end_time - rental.start_time).total_seconds()
        duration_minutes = max(1, int(duration_seconds // 60))
        rental.duration_minutes = duration_minutes

        # Gesamtpreis berechnen: Grundpreis + (Minuten * Minutenpreis)
        total_price = rental.scooter.base_price + (duration_minutes * rental.scooter.price_per_minute)
        rental.total_price = round(total_price, 2)

        # Miete abschliessen und Scooter wieder freigeben
        rental.status = "completed"
        rental.scooter.status = "available"

        db.session.commit()

        flash(f"Fahrt beendet. Preis: CHF {rental.total_price}")
        return redirect(url_for("dashboard"))


    # ----------------------------------------------------------
    # Route: Logout
    # Beendet die aktuelle Session und leitet zur Startseite weiter.
    # ----------------------------------------------------------
    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Erfolgreich ausgeloggt.")
        return redirect(url_for("home"))


    # ==========================================================
    # API-Endpunkte (RESTful)
    # Authentifizierung via Bearer Token (kein Browser erforderlich)
    # ==========================================================

    # ----------------------------------------------------------
    # API-Endpunkt: POST /api/login
    # Authentifiziert einen Benutzer anhand von Benutzername und
    # Passwort. Generiert einen zufälligen Token (64 Zeichen hex)
    # und speichert ihn in der Datenbank.
    # Rückgabe: JSON mit Token bei Erfolg, Fehler bei Misserfolg.
    # ----------------------------------------------------------
    @app.route("/api/login", methods=["POST"])
    def api_login():
        data = request.get_json()

        # Prüft ob ein JSON-Body mitgeschickt wurde
        if not data:
            return jsonify({"error": "JSON body fehlt"}), 400

        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        # Passwort-Hash prüfen
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Ungültige Zugangsdaten"}), 401

        # Neuen Token generieren und in der Datenbank speichern
        # secrets.token_hex(32) erzeugt einen kryptografisch sicheren Token
        token = secrets.token_hex(32)
        user.api_token = token
        db.session.commit()

        return jsonify({
            "message": "Login erfolgreich",
            "token": token
        })


    # ----------------------------------------------------------
    # API-Endpunkt: GET /api/scooters
    # Gibt alle Scooter der Datenbank als JSON-Array zurück.
    # Authentifizierung via Bearer Token erforderlich.
    # ----------------------------------------------------------
    @app.route("/api/scooters", methods=["GET"])
    def api_scooters():
        # Token-Authentifizierung prüfen
        user = get_api_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        scooters = Scooter.query.all()

        # Alle Scooter-Attribute als JSON-Array serialisieren
        return jsonify([
            {
                "id": s.id,
                "scooter_code": s.scooter_code,
                "qr_code": s.qr_code,
                "model": s.model,
                "battery_level": s.battery_level,
                "location": s.location,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "price_per_minute": s.price_per_minute,
                "base_price": s.base_price,
                "status": s.status,
                "provider_id": s.provider_id
            }
            for s in scooters
        ])


    # ----------------------------------------------------------
    # API-Endpunkt: GET /api/my-rentals
    # Gibt die Miethistorie des authentifizierten Benutzers zurück.
    # Sortiert nach ID absteigend (neueste Fahrten zuerst).
    # Authentifizierung via Bearer Token erforderlich.
    # ----------------------------------------------------------
    @app.route("/api/my-rentals", methods=["GET"])
    def api_my_rentals():
        # Token-Authentifizierung prüfen
        user = get_api_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        rentals = Rental.query.filter_by(user_id=user.id).order_by(Rental.id.desc()).all()

        # Fahrtdaten als JSON-Array serialisieren
        # Zeitstempel werden im ISO-8601-Format ausgegeben
        return jsonify([
            {
                "id": r.id,
                "scooter_code": r.scooter.scooter_code,
                "status": r.status,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "end_time": r.end_time.isoformat() if r.end_time else None,
                "duration_minutes": r.duration_minutes,
                "total_price": r.total_price
            }
            for r in rentals
        ])
