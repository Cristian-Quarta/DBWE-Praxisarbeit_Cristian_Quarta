from datetime import datetime
import secrets

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User, Scooter, Rental, PaymentMethod


def get_api_user():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]
    return User.query.filter_by(api_token=token).first()


def register_routes(app):
    @app.route("/")
    def home():
        scooters = Scooter.query.all()
        return render_template("home.html", scooters=scooters)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            role = request.form.get("role")

            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing_user:
                flash("Benutzername oder E-Mail existiert bereits.")
                return redirect(url_for("register"))

            if not role:
                role = "rider"

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

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash("Login erfolgreich.")
                return redirect(url_for("dashboard"))

            flash("Ungültiger Benutzername oder Passwort.")
            return redirect(url_for("login"))

        return render_template("login.html")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        if current_user.role == "provider":
            scooters = Scooter.query.filter_by(provider_id=current_user.id).all()
            return render_template("provider_dashboard.html", scooters=scooters)

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

    @app.route("/payment-methods", methods=["GET", "POST"])
    @login_required
    def payment_methods():
        if current_user.role != "rider":
            flash("Nur Fahrer können Zahlungsmittel verwalten.")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            card_holder = request.form.get("card_holder")
            card_number = request.form.get("card_number")
            expiry_month = request.form.get("expiry_month")
            expiry_year = request.form.get("expiry_year")
            brand = request.form.get("brand")

            if not card_holder or not card_number or not expiry_month or not expiry_year:
                flash("Bitte alle Pflichtfelder für das Zahlungsmittel ausfüllen.")
                return redirect(url_for("payment_methods"))

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

            if not scooter_code or not qr_code or not model or not battery_level or not location:
                flash("Bitte alle Pflichtfelder für den Scooter ausfüllen.")
                return redirect(url_for("add_scooter"))

            scooter = Scooter(
                scooter_code=scooter_code,
                qr_code=qr_code,
                model=model,
                battery_level=int(battery_level),
                location=location,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                price_per_minute=float(price_per_minute) if price_per_minute else 0.35,
                base_price=float(base_price) if base_price else 1.50,
                status=status if status else "available",
                provider_id=current_user.id
            )

            db.session.add(scooter)
            db.session.commit()

            flash("Scooter erfolgreich hinzugefügt.")
            return redirect(url_for("dashboard"))

        return render_template("add_scooter.html")

    @app.route("/provider/scooters/edit/<int:scooter_id>", methods=["GET", "POST"])
    @login_required
    def edit_scooter(scooter_id):
        if current_user.role != "provider":
            flash("Nur Anbieter dürfen Scooter verwalten.")
            return redirect(url_for("dashboard"))

        scooter = Scooter.query.get_or_404(scooter_id)

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

    @app.route("/provider/scooters/delete/<int:scooter_id>", methods=["POST"])
    @login_required
    def delete_scooter(scooter_id):
        if current_user.role != "provider":
            flash("Nur Anbieter dürfen Scooter verwalten.")
            return redirect(url_for("dashboard"))

        scooter = Scooter.query.get_or_404(scooter_id)

        if scooter.provider_id != current_user.id:
            flash("Keine Berechtigung.")
            return redirect(url_for("dashboard"))

        db.session.delete(scooter)
        db.session.commit()

        flash("Scooter gelöscht.")
        return redirect(url_for("dashboard"))

    @app.route("/rent/<int:scooter_id>", methods=["POST"])
    @login_required
    def rent_scooter(scooter_id):
        if current_user.role != "rider":
            flash("Nur Fahrer dürfen Scooter mieten.")
            return redirect(url_for("dashboard"))

        scooter = Scooter.query.get_or_404(scooter_id)
        qr_code_input = request.form.get("qr_code_input")

        payment_method = PaymentMethod.query.filter_by(user_id=current_user.id).first()
        if not payment_method:
            flash("Vor dem Mieten muss mindestens ein Zahlungsmittel hinterlegt werden.")
            return redirect(url_for("payment_methods"))

        active_rental = Rental.query.filter_by(user_id=current_user.id, status="active").first()
        if active_rental:
            flash("Es ist bereits eine aktive Miete vorhanden.")
            return redirect(url_for("dashboard"))

        if scooter.status != "available":
            flash("Dieser Scooter ist aktuell nicht verfügbar.")
            return redirect(url_for("dashboard"))

        if scooter.battery_level < 20:
            flash("Dieser Scooter kann wegen niedrigem Akkustand nicht gemietet werden.")
            return redirect(url_for("dashboard"))

        if qr_code_input != scooter.qr_code:
            flash("QR-Code ungültig. Der Scooter konnte nicht entsperrt werden.")
            return redirect(url_for("dashboard"))

        rental = Rental(
            user_id=current_user.id,
            scooter_id=scooter.id,
            start_time=datetime.utcnow(),
            status="active"
        )

        scooter.status = "rented"

        db.session.add(rental)
        db.session.commit()

        flash("Scooter erfolgreich gemietet und per QR-Code entsperrt.")
        return redirect(url_for("dashboard"))

    @app.route("/end_rental/<int:rental_id>", methods=["POST"])
    @login_required
    def end_rental(rental_id):
        rental = Rental.query.get_or_404(rental_id)

        if rental.user_id != current_user.id:
            flash("Keine Berechtigung für diese Miete.")
            return redirect(url_for("dashboard"))

        if rental.status != "active":
            flash("Diese Miete ist nicht mehr aktiv.")
            return redirect(url_for("dashboard"))

        rental.end_time = datetime.utcnow()

        duration_seconds = (rental.end_time - rental.start_time).total_seconds()
        duration_minutes = max(1, int(duration_seconds // 60))
        rental.duration_minutes = duration_minutes

        total_price = rental.scooter.base_price + (duration_minutes * rental.scooter.price_per_minute)
        rental.total_price = round(total_price, 2)

        rental.status = "completed"
        rental.scooter.status = "available"

        db.session.commit()

        flash(f"Fahrt beendet. Preis: CHF {rental.total_price}")
        return redirect(url_for("dashboard"))

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Erfolgreich ausgeloggt.")
        return redirect(url_for("home"))

    @app.route("/api/login", methods=["POST"])
    def api_login():
        data = request.get_json()

        if not data:
            return jsonify({"error": "JSON body fehlt"}), 400

        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Ungültige Zugangsdaten"}), 401

        token = secrets.token_hex(32)
        user.api_token = token
        db.session.commit()

        return jsonify({
            "message": "Login erfolgreich",
            "token": token
        })

    @app.route("/api/scooters", methods=["GET"])
    def api_scooters():
        user = get_api_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        scooters = Scooter.query.all()

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

    @app.route("/api/my-rentals", methods=["GET"])
    def api_my_rentals():
        user = get_api_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        rentals = Rental.query.filter_by(user_id=user.id).order_by(Rental.id.desc()).all()

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
