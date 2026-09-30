from datetime import date, time
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AvailabilityCreate(BaseModel):
    weekday: int = Field(ge=0, le=6, description="Monday=0, Sunday=6")
    start_time: time
    end_time: time
    slot_minutes: int = Field(default=30, ge=5, le=240)
    timezone: str = "Asia/Kolkata"
    is_active: bool = True

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return value

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, value: time, info):
        start = info.data.get("start_time")
        if start is not None and value <= start:
            raise ValueError("end_time must be later than start_time")
        return value


class AvailabilityResponse(AvailabilityCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    doctor_id: UUID


class SlotResponse(BaseModel):
    starts_at: str
    ends_at: str
    timezone: str
