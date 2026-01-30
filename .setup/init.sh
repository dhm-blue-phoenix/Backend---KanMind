#!/usr/bin/env bash
clear

# Mindestens Python 3.12 erforderlich (Django 6.0)
MIN_MAJOR=3
MIN_MINOR=12

# Priorisiert spezifische Python Versionen
if command -v python3.14 >/dev/null 2>&1; then
    PY="python3.14"
elif command -v python3.13 >/dev/null 2>&1; then
    PY="python3.13"
elif command -v python3.12 >/dev/null 2>&1; then
    PY="python3.12"
elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    echo "Python nicht gefunden. Installiere Python >= 3.12 und versuche es erneut."
    exit 1
fi

VER=$("$PY" --version 2>&1)
if [[ $VER =~ Python\ ([0-9]+)\.([0-9]+) ]]; then
    MAJOR="${BASH_REMATCH[1]}"
    MINOR="${BASH_REMATCH[2]}"

    if (( MAJOR < MIN_MAJOR || (MAJOR == MIN_MAJOR && MINOR < MIN_MINOR) )); then
        echo "Python >= $MIN_MAJOR.$MIN_MINOR erforderlich für Django 6.0. Gefunden: $VER"
        exit 1
    fi
else
    echo "Konnte Python-Version nicht parsen: $VER"
    exit 1
fi

echo "Python-Version OK: $VER"

# Flags / Parameter
CREATE_SUPERUSER=false
RUNSERVER=false
OPEN_VSCODE=false

for arg in "$@"; do
    case "${arg,,}" in
        --superuser) CREATE_SUPERUSER=true ;;
        --run)       RUNSERVER=true ;;
        --code)      OPEN_VSCODE=true ;;
    esac
done

echo "Starte Setup..."

# Virtuelle Umgebung erstellen
"$PY" -m venv .venv

# Aktivierung – plattformabhängig
VENV_ACTIVATE=""
if [[ -f ".venv/Scripts/activate" ]]; then
    # Windows (Git Bash, MSYS2, etc.)
    VENV_ACTIVATE=".venv/Scripts/activate"
elif [[ -f ".venv/bin/activate" ]]; then
    # Linux / macOS
    VENV_ACTIVATE=".venv/bin/activate"
else
    echo "Fehler: Aktivierungsskript nicht gefunden (.venv/bin/activate oder .venv/Scripts/activate)"
    exit 1
fi

source "$VENV_ACTIVATE"

# Nach der Aktivierung sollte python & pip nun aus der venv kommen
echo "Virtuelle Umgebung aktiviert → $(python --version)"

# Pip upgraden + Requirements installieren
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Django Migrations
python manage.py makemigrations
python manage.py migrate

# Optional: Superuser
if [ "$CREATE_SUPERUSER" = true ]; then
    echo "Erstelle Superuser..."
    python manage.py createsuperuser
fi

# Optional: VS Code öffnen
if [ "$OPEN_VSCODE" = true ]; then
    if command -v code >/dev/null 2>&1; then
        code .setup/KannMint.code-workspace 2>/dev/null || {
            echo "VS Code konnte nicht gestartet werden (code-Befehl fehlt oder Workspace nicht gefunden)"
        }
    else
        echo "VS Code ('code') nicht im PATH gefunden → wird übersprungen"
    fi
fi

# Optional: Server starten
if [ "$RUNSERVER" = true ]; then
    echo "Starte Django Development Server..."
    python manage.py runserver
fi