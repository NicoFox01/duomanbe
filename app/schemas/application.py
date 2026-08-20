from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.enums import CandidateStatus, ResidencyZone


class PresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(ge=1, le=5 * 1024 * 1024, description="Tamaño en bytes, máx 5MB")


class PresignResponse(BaseModel):
    upload_url: str
    path: str


class ApplicationCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=1, max_length=50)
    email: EmailStr
    zone: ResidencyZone
    target_role: str = Field(min_length=1, max_length=150)
    resume_path: str = Field(min_length=1, max_length=500)
    # Honeypot anti-spam.
    website: str | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    phone: str
    email: str
    zone: ResidencyZone
    target_role: str
    resume_url: str
    status: CandidateStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminApplicationOut(ApplicationOut):
    """Igual a ApplicationOut pero con URL firmada para ver/descargar el CV."""

    signed_resume_url: str | None = None


class ApplicationStatusUpdate(BaseModel):
    status: CandidateStatus