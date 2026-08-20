import html
import logging

import httpx

from app.core.config import Settings, get_settings
from app.schemas.quotation import QuotationOut

logger = logging.getLogger(__name__)

_RESEND_API_URL = "https://api.resend.com/emails"
_TIMEOUT_SECONDS = 10.0


def _row(label: str, value: str | None) -> str:
    if not value:
        return ""
    return (
        f'<tr><td style="padding:8px 12px;font-weight:600;color:#050505;'
        f'border-bottom:1px solid #eee">{html.escape(label)}</td>'
        f'<td style="padding:8px 12px;color:#333;border-bottom:1px solid #eee">'
        f"{html.escape(value)}</td></tr>"
    )


def _build_html(quotation: QuotationOut) -> str:
    services = ", ".join(quotation.services) if quotation.services else "—"
    rows = "".join(
        [
            _row("Nombre", quotation.full_name),
            _row("Teléfono", quotation.phone),
            _row("Email", quotation.email),
            _row("Empresa", quotation.company),
            _row("Ubicación", quotation.location),
            _row("Servicios", services),
            _row("Notas", quotation.notes),
            _row("ID", quotation.id),
        ]
    )
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:0 auto">'
        '<div style="background:#050505;color:#F2D20B;padding:16px 20px;border-radius:8px 8px 0 0">'
        "<h2 style=\"margin:0;font-size:18px\">Nueva solicitud de cotización</h2></div>"
        f'<table style="width:100%;border-collapse:collapse;background:#fff">{rows}</table>'
        '<p style="color:#888;font-size:12px;margin-top:12px">'
        "Mail automático generado por DUOMAN. Podés responder directamente al cliente.</p></div>"
    )


async def send_quotation_notification(quotation: QuotationOut) -> None:
    """Notifica una nueva cotización por email vía Resend.

    Best-effort: un fallo de envío se loguea pero nunca propaga la excepción,
    para no afectar la respuesta al cliente.
    """
    settings: Settings = get_settings()
    if not settings.notify_enabled:
        logger.debug("Notificaciones deshabilitadas: falta RESEND_API_KEY o NOTIFY_EMAIL_TO")
        return

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(
                _RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.NOTIFY_FROM_EMAIL,
                    "to": [settings.NOTIFY_EMAIL_TO],
                    "reply_to": quotation.email,
                    "subject": "Nueva solicitud de cotización - DUOMAN",
                    "html": _build_html(quotation),
                },
            )
            response.raise_for_status()
        logger.info("Notificación de cotización enviada (id=%s)", quotation.id)
    except Exception as exc:  # noqa: BLE001 - el mail nunca debe romper el flujo
        logger.warning("No se pudo enviar la notificación de cotización (id=%s): %s", quotation.id, exc)
