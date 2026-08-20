from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr | None = None
    phone: str = Field(min_length=1, max_length=50)
    role: str = Field(min_length=1, max_length=100)
    specialties: list[str] = Field(default_factory=list)


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: str | None
    phone: str
    role: str
    specialties: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime