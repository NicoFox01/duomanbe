# ============================================================
#  DUOMAN Backend - Helpers para PowerShell (venv nativo Windows)
# ============================================================
# Uso: dot-source este archivo una vez por sesion:
#     . .\tools.ps1
# Luego podes usar:
#     du-pip freeze
#     du-run
#     du-test
#     du-alembic current
# ============================================================

$script:ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:PY = Join-Path $script:ROOT ".venv-win\Scripts\python.exe"

function Test-DuVenv {
    if (-not (Test-Path $script:PY)) {
        Write-Error "No se encontro .venv-win. Crea el venv con: cd $script:ROOT; py -m venv .venv-win; .venv-win\Scripts\pip install -r requirements.txt"
        return $false
    }
    return $true
}

# Correr pip dentro del venv de Windows
function du-pip {
    if (-not (Test-DuVenv)) { return }
    & $script:PY -m pip @args
}

# Arrancar el backend (uvicorn con reload)
function du-run {
    if (-not (Test-DuVenv)) { return }
    Push-Location $script:ROOT
    try {
        & $script:PY -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    } finally {
        Pop-Location
    }
}

# Correr los tests
function du-test {
    if (-not (Test-DuVenv)) { return }
    Push-Location $script:ROOT
    try {
        & $script:PY -m pytest @args
    } finally {
        Pop-Location
    }
}

# Ejecutar comandos de Alembic
function du-alembic {
    if (-not (Test-DuVenv)) { return }
    Push-Location $script:ROOT
    try {
        & $script:PY -m alembic @args
    } finally {
        Pop-Location
    }
}

# Ver el freeze de paquetes instalados en el venv
function du-freeze {
    if (-not (Test-DuVenv)) { return }
    & $script:PY -m pip freeze
}

Write-Host "Helpers DUOMAN cargados. Probá: du-freeze  |  du-pip install ...  |  du-run  |  du-test"