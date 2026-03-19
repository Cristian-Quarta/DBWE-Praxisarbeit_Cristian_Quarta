# ==============================================================
# run.py – Einstiegspunkt der ScootNow Applikation
# Startet den Flask Development Server (nur für lokale Entwicklung)
# In der Produktion wird die App durch Gunicorn gestartet:
# gunicorn -w 4 -b 0.0.0.0:8000 run:app
# Autor: Cristian Quarta | DBWE.TA1A.PA | 2026
# ==============================================================

from app import create_app

# Erstellt die Flask-Applikation über die Application Factory.
# Alle Konfigurationen, Erweiterungen und Routen werden dabei
# in __init__.py initialisiert.
app = create_app()

if __name__ == "__main__":
    # Startet den integrierten Flask-Entwicklungsserver.
    # host="0.0.0.0"  – erreichbar von allen Netzwerkinterfaces
    # port=5000       – Standardport für Flask-Entwicklung
    # debug=True      – aktiviert Auto-Reload bei Codeänderungen
    #                   und zeigt detaillierte Fehlermeldungen.
    #                   ACHTUNG: debug=True nie in Produktion verwenden!
    app.run(host="0.0.0.0", port=5000, debug=True)
