from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MedicalRecordCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=40)
    content: str | None = Field(default=None, max_length=50000)
    file_name: str | None = Field(default=None, max_length=255)
    mime_type: str | None = Field(default=None, max_length=100)


class MedicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    category: str
    content: str | None
    created_at: datetime
    updated_at: datetime
