Clear-Host

# Ensure required Python version
$RequiredVersion = '3.12'
try {
    $pyOutput = & python --version 2>&1
} catch {
    Write-Host "Python not found in PATH. Install Python $RequiredVersion and try again." -ForegroundColor Red
    exit 1
}
if ($pyOutput -notmatch "Python $RequiredVersion") {
    Write-Host "Python $RequiredVersion is required. Found: $pyOutput" -ForegroundColor Red
    exit 1
}

# Parameter-Flags
$CreateSuperuser = $false
$RunServer = $false
$OpenVSCode = $false

# Parameter prüfen
foreach ($arg in $args) {
    switch ($arg) {
        "--superuser" { $CreateSuperuser = $true }
        "--run"       { $RunServer = $true }
        "--code"      { $OpenVSCode = $true }
    }
}

Write-Host "Starte Setup..." -ForegroundColor Cyan

# Virtuelle Umgebung erstellen
python -m venv .venv
& ".venv\Scripts\Activate.ps1"

pip install -r requirements.txt

# Ordner + __init__.py
New-Item -ItemType Directory -Path "board_app\migrations" -Force | Out-Null
New-Item -ItemType File -Path "board_app\migrations\__init__.py" -Force | Out-Null

# Django Migrations
python manage.py makemigrations
python manage.py migrate

# Optional: Superuser
if ($CreateSuperuser) {
    Write-Host "Erstelle Superuser..." -ForegroundColor Yellow
    python manage.py createsuperuser
}

# Optional: VS Code starten
if ($OpenVSCode) {
    Write-Host "Starte VS Code..." -ForegroundColor Green
    code ".setup\KannMint.code-workspace"
}

# Optional: Server starten
if ($RunServer) {
    Write-Host "Starte Django Server..." -ForegroundColor Green
    python manage.py runserver
}