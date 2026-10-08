from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MedicalRecordCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=40)
    content: str | None = Field(default=None, max_length=50000)
    file_name: str | None = Field(default=None, max_length=255)
    mime_type: str | None = Field(default=None, max_length=100)


class MedicalRecordUploadRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=40)
    file_name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=100)


class MedicalRecordUploadResponse(BaseModel):
    record_id: UUID
    upload_url: str
    storage_key: str
    expires_in: int


class MedicalRecordCompleteRequest(BaseModel):
    pass


class MedicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    category: str
    content: str | None
    file_name: str | None
    mime_type: str | None
    file_size: int | None
    upload_completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
