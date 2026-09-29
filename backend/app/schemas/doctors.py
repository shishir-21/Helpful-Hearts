from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

ProfileStatus = Literal["draft", "submitted", "verified", "rejected"]
VerificationStatus = Literal["unverified", "pending", "verified", "rejected"]
AffiliationStatus = Literal["current", "former", "pending"]


class HospitalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    address: str = Field(min_length=3, max_length=1000)
    city: str = Field(min_length=2, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str = Field(default="India", min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    is_demo: bool = True
    source_name: str = Field(default="Helpful Hearts demo dataset", min_length=2, max_length=180)
    source_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def coordinates_are_a_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class HospitalResponse(HospitalCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class DoctorCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    specialty: str = Field(min_length=2, max_length=120)
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


class AffiliationCreate(BaseModel):
    hospital_id: UUID
    role_title: str | None = Field(default=None, max_length=120)
    status: AffiliationStatus = "current"
    start_date: date | None = None
    end_date: date | None = None
    is_demo: bool = True
    source_name: str = Field(default="Helpful Hearts demo dataset", min_length=2, max_length=180)
    source_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        if self.status == "current" and self.end_date is not None:
            raise ValueError("current affiliations cannot have an end_date")
        return self


class AffiliationResponse(AffiliationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    doctor_id: UUID
    hospital: HospitalResponse
    created_at: datetime


class DoctorAdminResponse(DoctorCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    credentials: list[CredentialResponse]
    affiliations: list[AffiliationResponse]
    created_at: datetime
    updated_at: datetime


class DoctorPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str
    specialty: str
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
    credentials: list[CredentialResponse]
    affiliations: list[AffiliationResponse]
