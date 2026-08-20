from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.enums import QuotationStatus


class QuotationCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    phone: str = Field(min_length=1, max_length=50)
    company: str | None = Field(default=None, max_length=150)
    location: str = Field(min_length=1, max_length=200)
    services: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=5000)
    # Honeypot anti-spam: los bots suelen completarlo.
    website: str | None = None


class QuotationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: str
    phone: str
    company: str | None
    location: str
    services: list[str]
    notes: str | None
    status: QuotationStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime


class QuotationStatusUpdate(BaseModel):
    status: QuotationStatus