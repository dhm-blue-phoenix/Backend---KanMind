Clear-Host

# Mindestens Python 3.12 erforderlich (Django 6.0)
$MinMajor = 3
$MinMinor = 12

try {
    $pyOutput = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Host "Python nicht im PATH gefunden. Installiere Python >= 3.12 und versuche es erneut." -ForegroundColor Red
    exit 1
}

# Version parsen
if ($pyOutput -match "Python (\d+)\.(\d+)") {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    
    if ($major -lt $MinMajor -or ($major -eq $MinMajor -and $minor -lt $MinMinor)) {
        Write-Host "Python >= $MinMajor.$MinMinor erforderlich für Django 6.0. Gefunden: $pyOutput" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Konnte Python-Version nicht parsen: $pyOutput" -ForegroundColor Red
    exit 1
}

Write-Host "Python-Version OK: $pyOutput" -ForegroundColor Green

# Parameter-Flags
$CreateSuperuser = $false
$RunServer       = $false
$OpenVSCode      = $false

# Parameter prüfen
foreach ($arg in $args) {
    switch ($arg.ToLower()) {
        "--superuser" { $CreateSuperuser = $true }
        "--run"       { $RunServer       = $true }
        "--code"      { $OpenVSCode      = $true }
    }
}

Write-Host "Starte Setup..." -ForegroundColor Cyan

# Virtuelle Umgebung erstellen (nutzt den gerade geprüften python)
python -m venv .venv

# Aktivieren
& ".venv\Scripts\Activate.ps1"

# Requirements installieren
pip install --upgrade pip
pip install -r requirements.txt

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