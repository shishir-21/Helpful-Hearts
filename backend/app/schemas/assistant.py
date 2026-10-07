from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=160)

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime

class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role: str
    content: str
    created_at: datetime
