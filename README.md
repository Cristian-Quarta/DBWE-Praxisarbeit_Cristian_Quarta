# ScootNow

ScootNow ist eine webbasierte E-Scooter-Plattform auf Basis von Flask und PostgreSQL.

## Funktionen
- Registrierung und Login
- Rollen: Rider und Provider
- Scooter-Verwaltung für Provider
- Scooter mieten und Fahrt beenden
- Preisberechnung
- QR-Code-Simulation
- Zahlungsmittel speichern
- REST API mit Token-Authentifizierung

## Technologien
- Python
- Flask
- PostgreSQL
- SQLAlchemy
- Gunicorn
- Bootstrap

## Lokales Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
