from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AppointmentCreate(BaseModel):
    doctor_id: UUID
    starts_at: datetime
    reason: str | None = Field(default=None, max_length=2000)


class AppointmentCancellation(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class AppointmentReschedule(BaseModel):
    starts_at: datetime


class AppointmentDoctorStatusUpdate(BaseModel):
    status: Literal["completed", "cancelled", "no_show"]
    note: str | None = Field(default=None, max_length=1000)


class AppointmentStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    appointment_id: UUID
    changed_by_user_id: UUID | None
    previous_status: str | None
    new_status: str
    event: str
    note: str | None
    created_at: datetime


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    starts_at: datetime
    ends_at: datetime
    status: str
    reason: str | None
    booking_reference: str
    created_at: datetime
