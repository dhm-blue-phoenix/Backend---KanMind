#!/usr/bin/env bash
clear

# Mindestens Python 3.12 erforderlich (Django 6.0)
MIN_MAJOR=3
MIN_MINOR=12

# Python-Befehl finden und Version prüfen
if command -v python3.14 >/dev/null 2>&1; then
    PY=python3.14
elif command -v python3.13 >/dev/null 2>&1; then
    PY=python3.13
elif command -v python3.12 >/dev/null 2>&1; then
    PY=python3.12
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "Python nicht gefunden. Installiere Python >= 3.12 und versuche es erneut."
    exit 1
fi

VER=$($PY --version 2>&1)
if [[ $VER =~ Python\ ([0-9]+)\.([0-9]+) ]]; then
    MAJOR=${BASH_REMATCH[1]}
    MINOR=${BASH_REMATCH[2]}

    if (( MAJOR < MIN_MAJOR || (MAJOR == MIN_MAJOR && MINOR < MIN_MINOR) )); then
        echo "Python >= $MIN_MAJOR.$MIN_MINOR erforderlich für Django 6.0. Gefunden: $VER"
        exit 1
    fi
else
    echo "Konnte Python-Version nicht parsen: $VER"
    exit 1
fi

echo "Python-Version OK: $VER"

CREATE_SUPERUSER=false
RUNSERVER=false
OPEN_VSCODE=false

# Parameter prüfen (case-insensitive mit ${arg,,})
for arg in "$@"; do
    case "${arg,,}" in
        --superuser) CREATE_SUPERUSER=true ;;
        --run)       RUNSERVER=true ;;
        --code)      OPEN_VSCODE=true ;;
    esac
done

echo "Starte Setup..."

# Virtuelle Umgebung mit dem gefundenen Python erstellen
$PY -m venv .venv
source .venv/bin/activate

# Pip upgraden + Requirements
pip install --upgrade pip
pip install -r requirements.txt

# Migrations-Ordner + __init__.py
mkdir -p board_app/migrations
touch board_app/migrations/__init__.py

# Django Migrations
python manage.py makemigrations
python manage.py migrate

# Optional: Superuser
if [ "$CREATE_SUPERUSER" = true ]; then
    python manage.py createsuperuser
fi

# Optional: VS Code öffnen
if [ "$OPEN_VSCODE" = true ]; then
    code .setup/KannMint.code-workspace 2>/dev/null || {
        echo "VS Code konnte nicht gestartet werden – ist 'code' im PATH?"
    }
fi

# Optional: Server starten
if [ "$RUNSERVER" = true ]; then
    python manage.py runserver
fi
