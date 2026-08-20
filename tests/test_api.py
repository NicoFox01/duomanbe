"""Pruebas de unidad y de la API.

Las pruebas que tocan Supabase se corren solo si el .env está completo
(para no romper el pipeline sin credenciales).
"""
import os
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _supabase_ok() -> bool:
    from app.core.config import get_settings

    s = get_settings()
    return bool(s.SUPABASE_URL and s.SUPABASE_SERVICE_ROLE_KEY and s.CRON_SECRET)


@pytest.mark.skipif(not _supabase_ok(), reason="Supabase no configurado")
def test_login_admin(client):
    from app.core.config import get_settings

    settings = get_settings()
    email = os.environ.get("ADMIN_EMAIL") or settings.ADMIN_EMAIL or ""
    password = os.environ.get("ADMIN_PASSWORD") or settings.ADMIN_PASSWORD or ""
    email = unquote(email)
    if not email or not password:
        pytest.skip("Definí ADMIN_EMAIL/ADMIN_PASSWORD (env o .env) para este test")

    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"]
    assert body["user"]["email"] == email


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_cron_keepalive_requires_secret(client):
    r = client.post("/api/v1/cron/keepalive")
    assert r.status_code in (401, 503)


def test_enums_values():
    from app.schemas.enums import CandidateStatus, QuotationStatus, ResidencyZone

    assert QuotationStatus.RECHAZADA.value == "Rechazada"
    assert CandidateStatus.CONTRATADO.value == "Contratado"
    assert ResidencyZone.GBA_NORTE.value == "GBA Norte"


def test_presign_rejects_bad_extension():
    from app.api.routers.applications import ALLOWED_EXTENSIONS

    assert ".pdf" in ALLOWED_EXTENSIONS
    assert ".exe" not in ALLOWED_EXTENSIONS