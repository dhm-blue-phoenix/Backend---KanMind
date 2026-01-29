#!/bin/bash

clear

CREATE_SUPERUSER=false
RUNSERVER=false
OPEN_VSCODE=false

# Parameter prüfen
for arg in "$@"; do
    if [ "$arg" = "--superuser" ]; then
        CREATE_SUPERUSER=true
    fi
    if [ "$arg" = "--run" ]; then
        RUNSERVER=true
    fi
    if [ "$arg" = "--code" ]; then
        OPEN_VSCODE=true
    fi
done

echo "Starte Setup..."

# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate

# Requirements installieren
pip install -r requirements.txt

# Ordner + __init__.py
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
    code .
fi

# Optional: Server starten
if [ "$RUNSERVER" = true ]; then
    python manage.py runserver
fi