from datetime import datetime, timezone
from pathlib import PurePosixPath
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import DbClientDep
from app.core.config import get_settings
from app.repositories import applications as repo
from app.schemas.application import ApplicationCreate, ApplicationOut, PresignRequest, PresignResponse
from app.schemas.enums import CandidateStatus
from app.utils.ratelimit import make_rate_limiter

router = APIRouter(prefix="/applications", tags=["applications"])

_settings = get_settings()
_application_limiter = make_rate_limiter(max_requests=10, window_seconds=60)

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_SIZE = 5 * 1024 * 1024


@router.post("/presign-resume", response_model=PresignResponse)
async def presign_resume(
    payload: PresignRequest,
    request: Request,
    client: DbClientDep,
    _: None = Depends(_application_limiter),
) -> PresignResponse:
    ext = PurePosixPath(payload.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no permitido. Solo .pdf, .doc o .docx",
        )
    if payload.size > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo supera el tamaño máximo de 5MB",
        )

    path = f"{uuid4().hex}{ext}"
    upload_url = await repo.create_bucket_path(client, _settings.BUCKET_RESUMES, path)
    return PresignResponse(upload_url=upload_url, path=path)


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    request: Request,
    client: DbClientDep,
    _: None = Depends(_application_limiter),
) -> ApplicationOut:
    if payload.website:
        fake = payload.model_dump(exclude={"website", "resume_path"})
        row = {
            **fake,
            "zone": payload.zone,
            "target_role": payload.target_role,
            "resume_url": "spam-descartado",
            "status": CandidateStatus.POSTULADO.value,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "id": "00000000-0000-0000-0000-000000000000",
        }
        return ApplicationOut.model_validate(row)

    row = await repo.insert_application(
        client,
        {
            "full_name": payload.full_name,
            "phone": payload.phone,
            "email": payload.email,
            "zone": payload.zone.value,
            "target_role": payload.target_role,
            "resume_url": payload.resume_path,
        },
    )
    return ApplicationOut.model_validate(row)