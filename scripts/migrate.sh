#!/usr/bin/env bash
# Aplica las migraciones de esquema (code-first) a Supabase.
set -e
cd "$(dirname "$0")"

exec .venv/bin/python -m alembic upgrade head