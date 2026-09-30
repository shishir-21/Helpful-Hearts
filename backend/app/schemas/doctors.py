from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

ProfileStatus = Literal["draft", "submitted", "verified", "rejected"]
VerificationStatus = Literal["unverified", "pending", "verified", "rejected"]


class DoctorCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    specialty: str = Field(min_length=2, max_length=120)
    hospital_name: str | None = Field(default=None, max_length=180)
    biography: str | None = Field(default=None, max_length=10000)
    years_experience: int | None = Field(default=None, ge=0, le=80)
    languages: str | None = Field(default=None, max_length=300)
    public_phone: str | None = Field(default=None, max_length=30)
    public_email: EmailStr | None = None
    booking_instructions: str | None = Field(default=None, max_length=3000)
    registration_number: str | None = Field(default=None, max_length=100)
    registration_council: str | None = Field(default=None, max_length=180)
    registration_state: str | None = Field(default=None, max_length=100)
    registration_year: int | None = Field(default=None, ge=1900, le=2100)
    profile_status: ProfileStatus = "draft"
    is_demo: bool = True
    source_name: str = Field(default="Helpful Hearts demo dataset", min_length=2, max_length=180)
    source_url: str | None = Field(default=None, max_length=500)


class CredentialCreate(BaseModel):
    degree: str = Field(min_length=2, max_length=180)
    institution: str | None = Field(default=None, max_length=180)
    year_awarded: int | None = Field(default=None, ge=1900, le=2100)
    verification_status: VerificationStatus = "unverified"
    verification_note: str | None = Field(default=None, max_length=3000)
    source_name: str = Field(default="Doctor-submitted", min_length=2, max_length=180)
    source_url: str | None = Field(default=None, max_length=500)


class CredentialResponse(CredentialCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    doctor_id: UUID
    verified_at: datetime | None
    created_at: datetime


class PublicCredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    degree: str
    institution: str | None
    year_awarded: int | None
    verification_status: VerificationStatus
    verified_at: datetime | None
    source_name: str
    source_url: str | None


class DoctorAdminResponse(DoctorCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    credentials: list[CredentialResponse]
    created_at: datetime
    updated_at: datetime


class DoctorPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str
    specialty: str
    hospital_name: str | None
    biography: str | None
    years_experience: int | None
    languages: str | None
    public_phone: str | None
    public_email: EmailStr | None
    booking_instructions: str | None
    profile_status: ProfileStatus
    is_demo: bool
    source_name: str
    source_url: str | None
    updated_at: datetime
    credentials: list[PublicCredentialResponse]
