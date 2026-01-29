@echo off
cls

## Parameter prüfen
set CREATE_SUPERUSER=false
set OPEN_VSCODE=false
set RUNSERVER=false

for %%A in (%*) do (
    if "%%A"=="--superuser" set CREATE_SUPERUSER=true
    if "%%A"=="--run" set RUNSERVER=true
    if "%%A"=="--code" set OPEN_VSCODE=true
)

echo Starte Setup...

## Virtuelle Umgebung erstellen
python -m venv venv
venv\Scripts\activate

## Requirements installieren
pip install -r requirements.txt

## Ordner + __init__.py
mkdir board_app\migrations 2>nul
type nul > board_app\migrations\__init__.py

## Django Migrations
python manage.py makemigrations
python manage.py migrate

## Optional: Superuser
if "%CREATE_SUPERUSER%"=="true" (
    python manage.py createsuperuser
)

## Optional: VS Code öffnen
if "%OPEN_VSCODE%"=="true" (
    code .
)

## Optional: Server starten
if "%RUNSERVER%"=="true" (
    python manage.py runserver
)