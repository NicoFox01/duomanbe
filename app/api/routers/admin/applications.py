from fastapi import APIRouter, HTTPException, Response, status
from pydantic import UUID4

from app.api.deps import AdminClaimsDep, DbClientDep
from app.core.config import get_settings
from app.repositories import applications as repo
from app.schemas.application import AdminApplicationOut, ApplicationStatusUpdate
from app.schemas.enums import CandidateStatus

router = APIRouter(prefix="/applications", tags=["admin-applications"])

_settings = get_settings()


@router.get("", response_model=list[AdminApplicationOut])
async def list_applications(
    _: AdminClaimsDep,
    client: DbClientDep,
    status_filter: CandidateStatus | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AdminApplicationOut]:
    rows = await repo.list_applications(
        client,
        bucket=_settings.BUCKET_RESUMES,
        status=status_filter.value if status_filter else None,
        search=search,
        limit=min(limit, 200),
        offset=offset,
    )
    return [AdminApplicationOut.model_validate(r) for r in rows]


@router.patch("/{application_id}/status", response_model=AdminApplicationOut)
async def update_status(
    application_id: UUID4,
    payload: ApplicationStatusUpdate,
    _: AdminClaimsDep,
    client: DbClientDep,
) -> AdminApplicationOut:
    row = await repo.update_application_status(client, str(application_id), payload.status.value)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postulación no encontrada")
    row["signed_resume_url"] = await repo.get_signed_url(
        client, _settings.BUCKET_RESUMES, row.get("resume_url", "")
    )
    return AdminApplicationOut.model_validate(row)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: UUID4,
    _: AdminClaimsDep,
    client: DbClientDep,
) -> Response:
    ok = await repo.soft_delete_application(client, str(application_id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postulación no encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)