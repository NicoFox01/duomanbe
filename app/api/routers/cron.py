import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DbClientDep
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cron", tags=["cron"])


class KeepaliveResponse(BaseModel):
    ok: bool = True
    inserted_at: str


@router.post("/keepalive", response_model=KeepaliveResponse)
async def keepalive(
    client: DbClientDep,
    authorization: str | None = Header(default=None),
    x_cron_secret: str | None = Header(default=None, alias="X-Cron-Secret"),
) -> KeepaliveResponse:
    """Inserta la hora actual en `cronjobs` para evitar que la BBDD se pause.

    Disparado diariamente a las 08:00 AM por Vercel Cron.
    """
    settings = get_settings()

    provided = ""
    if x_cron_secret:
        provided = x_cron_secret
    elif authorization:
        provided = authorization.removeprefix("Bearer ").strip()

    if not settings.CRON_SECRET or provided != settings.CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron secret",
        )

    now = datetime.now(timezone.utc)
    await client.table("cronjobs").insert({"executed_at": now.isoformat()}).execute()
    logger.info("Keepalive ejecutado en %s", now.isoformat())

    return KeepaliveResponse(inserted_at=now.isoformat())