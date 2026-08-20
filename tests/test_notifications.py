"""Pruebas del servicio de notificaciones (Resend) y su integración en el router de cotizaciones."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.schemas.quotation import QuotationOut
from app.services import notifications

_RESEND_URL = "https://api.resend.com/emails"


def _settings(**overrides) -> Settings:
    values: dict = {
        "RESEND_API_KEY": "re_test_key",
        "NOTIFY_FROM_EMAIL": "onboarding@resend.dev",
        "NOTIFY_EMAIL_TO": "avisos@test.com",
    }
    values.update(overrides)
    return Settings(**values)


def _quotation() -> QuotationOut:
    now = datetime.now(timezone.utc)
    return QuotationOut(
        id="11111111-1111-1111-1111-111111111111",
        full_name="Juan Pérez <script>",
        email="juan@example.com",
        phone="11 5555-5555",
        company="Acme SA",
        location="CABA",
        services=["Electricidad", "Plomería"],
        notes="Urgencia en tablero <b>",
        status="Pendiente",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


class _FakeResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=httpx.Request("POST", _RESEND_URL),
                response=httpx.Response(self.status_code),
            )


@pytest.mark.asyncio
async def test_sin_api_key_no_envia_nada(monkeypatch):
    calls: list = []

    async def fake_post(self, url, **kwargs):
        calls.append(url)
        return _FakeResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(notifications, "get_settings", lambda: _settings(RESEND_API_KEY=""))

    await notifications.send_quotation_notification(_quotation())
    assert calls == []


@pytest.mark.asyncio
async def test_sin_destinatario_no_envia_nada(monkeypatch):
    calls: list = []

    async def fake_post(self, url, **kwargs):
        calls.append(url)
        return _FakeResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(notifications, "get_settings", lambda: _settings(NOTIFY_EMAIL_TO=""))

    await notifications.send_quotation_notification(_quotation())
    assert calls == []


@pytest.mark.asyncio
async def test_arma_el_mail_correcto(monkeypatch):
    captured: dict = {}

    async def fake_post(self, url, *, headers=None, json=None):
        captured.update({"url": url, "headers": headers, "json": json})
        return _FakeResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(notifications, "get_settings", lambda: _settings())

    await notifications.send_quotation_notification(_quotation())

    assert captured["url"] == _RESEND_URL
    assert captured["headers"]["Authorization"] == "Bearer re_test_key"
    body = captured["json"]
    assert body["from"] == "onboarding@resend.dev"
    assert body["to"] == ["avisos@test.com"]
    assert body["reply_to"] == "juan@example.com"
    assert "Nueva solicitud de cotización" in body["subject"]
    # Datos del cliente presentes y HTML de input usuario escapado.
    assert "Juan Pérez" in body["html"]
    assert "<script>" not in body["html"]
    assert "juan@example.com" in body["html"]
    assert "Electricidad, Plomería" in body["html"]


@pytest.mark.asyncio
async def test_fallo_de_envio_no_propaga(monkeypatch):
    async def fake_post(self, url, **kwargs):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(notifications, "get_settings", lambda: _settings())

    await notifications.send_quotation_notification(_quotation())


# ---------------------------------------------------------------
# Integración del router: POST /quotations notifica solo si persiste
# ---------------------------------------------------------------

_PAYLOAD = {
    "full_name": "Juan Pérez",
    "email": "juan@example.com",
    "phone": "11 5555-5555",
    "company": "Acme SA",
    "location": "CABA",
    "services": ["Electricidad"],
    "notes": "Necesito presupuesto",
}


@pytest.fixture()
def api_con_mocks(monkeypatch):
    from app.api.deps import get_db_client

    async def fake_insert(_client, data):
        now = datetime.now(timezone.utc)
        return {
            "id": "22222222-2222-2222-2222-222222222222",
            **data,
            "status": "Pendiente",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

    notified: list[QuotationOut] = []

    async def fake_notify(quotation: QuotationOut) -> None:
        notified.append(quotation)

    async def override_db():
        return object()

    monkeypatch.setattr("app.repositories.quotations.insert_quotation", fake_insert)
    monkeypatch.setattr("app.api.routers.quotations.send_quotation_notification", fake_notify)
    app.dependency_overrides[get_db_client] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client, notified
    finally:
        app.dependency_overrides.clear()


def test_cotizacion_persiste_y_notifica(api_con_mocks):
    client, notified = api_con_mocks

    r = client.post("/api/v1/quotations", json=_PAYLOAD)

    assert r.status_code == 201, r.text
    assert len(notified) == 1
    assert notified[0].full_name == "Juan Pérez"
    assert notified[0].email == "juan@example.com"


def test_honeypot_responde_pero_no_notifica(api_con_mocks):
    client, notified = api_con_mocks

    r = client.post("/api/v1/quotations", json={**_PAYLOAD, "website": "http://spam.example"})

    assert r.status_code == 201
    assert notified == []
