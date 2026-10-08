from typing import TYPE_CHECKING
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.doctor_credential import DoctorCredential
    from app.models.user import User


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    specialty: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    hospital_name: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    biography: Mapped[str | None] = mapped_column(Text)
    years_experience: Mapped[int | None] = mapped_column(Integer)
    languages: Mapped[str | None] = mapped_column(String(300), comment="Comma-separated language names")
    public_phone: Mapped[str | None] = mapped_column(String(30))
    public_email: Mapped[str | None] = mapped_column(String(320))
    booking_instructions: Mapped[str | None] = mapped_column(Text)
    registration_number: Mapped[str | None] = mapped_column(String(100))
    registration_council: Mapped[str | None] = mapped_column(String(180))
    registration_state: Mapped[str | None] = mapped_column(String(100))
    registration_year: Mapped[int | None] = mapped_column(Integer)
    profile_status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_name: Mapped[str] = mapped_column(String(180), nullable=False, default="Helpful Hearts demo dataset")
    source_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="doctor_profile")
    credentials: Mapped[list["DoctorCredential"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
