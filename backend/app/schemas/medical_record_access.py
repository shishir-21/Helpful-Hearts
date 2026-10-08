from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MedicalRecordAccessRequest(BaseModel):
    doctor_id: UUID = Field(description="Doctor profile ID to grant access to")


class MedicalRecordAccessResponse(BaseModel):
    doctor_id: UUID
    medical_record_id: UUID
    created_at: datetime
