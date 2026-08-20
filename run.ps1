# Arranca la API en desarrollo usando el venv nativo de Windows.
# Uso:  .\run.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv-win\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "No se encontro el venv de Windows. Crealo con: py -m venv .venv-win"
    exit 1
}

& $python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload