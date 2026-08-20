from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import DbClientDep
from app.repositories import quotations as repo
from app.schemas.enums import QuotationStatus
from app.schemas.quotation import QuotationCreate, QuotationOut
from app.services.notifications import send_quotation_notification
from app.utils.ratelimit import make_rate_limiter

router = APIRouter(prefix="/quotations", tags=["quotations"])

_quotation_limiter = make_rate_limiter(max_requests=10, window_seconds=60)


def _fake_report(payload: QuotationCreate) -> QuotationOut:
    """Respuesta de éxito silenciosa para bots que completan el honeypot."""
    return QuotationOut(
        id="00000000-0000-0000-0000-000000000000",
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        company=payload.company,
        location=payload.location,
        services=payload.services,
        notes=payload.notes,
        status=QuotationStatus.PENDIENTE,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@router.post("", response_model=QuotationOut, status_code=status.HTTP_201_CREATED)
async def create_quotation(
    payload: QuotationCreate,
    request: Request,
    client: DbClientDep,
    _: None = Depends(_quotation_limiter),
) -> QuotationOut:
    if payload.website:
        return _fake_report(payload)

    row = await repo.insert_quotation(
        client,
        {
            "full_name": payload.full_name,
            "email": payload.email,
            "phone": payload.phone,
            "company": payload.company,
            "location": payload.location,
            "services": payload.services,
            "notes": payload.notes,
        },
    )
    quotation = QuotationOut.model_validate(row)
    await send_quotation_notification(quotation)
    return quotation