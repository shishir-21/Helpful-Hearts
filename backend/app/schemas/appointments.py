from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class AppointmentCreate(BaseModel):
    doctor_id: UUID
    starts_at: datetime
    reason: str | None = Field(default=None, max_length=2000)

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
