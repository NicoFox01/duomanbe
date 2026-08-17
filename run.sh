#!/usr/bin/env bash
# Arranca la API en desarrollo.
# --loop asyncio: evita problemas de uvloop en WSL/Windows.
set -e
cd "$(dirname "$0")"

exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --loop asyncio --reload