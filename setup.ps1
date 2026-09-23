# One-shot environment setup for Windows PowerShell.
#   .\setup.ps1
# If script execution is blocked, run once as admin:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

$ErrorActionPreference = "Stop"

Write-Host "==> Creating virtual environment in .venv ..."
python -m venv .venv

Write-Host "==> Activating .venv ..."
. .\.venv\Scripts\Activate.ps1

Write-Host "==> Upgrading pip ..."
pip install --upgrade pip -q

Write-Host "==> Installing requirements.txt ..."
pip install -r requirements.txt -q

Write-Host "==> Installing project in editable mode (so 'hhgoa_fraud' is importable) ..."
pip install -e . -q

if (-not (Test-Path ".env")) {
    Write-Host "==> Creating .env from .env.example ..."
    Copy-Item ".env.example" ".env"
} else {
    Write-Host "==> .env already exists, leaving it untouched."
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Activate the environment in new shells with: .\.venv\Scripts\Activate.ps1"
Write-Host "Next: place the HHGOA dataset files under data\, then run:"
Write-Host "  python scripts\00_check_setup.py"
