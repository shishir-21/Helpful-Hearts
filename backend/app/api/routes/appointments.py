from datetime import datetime, timedelta, timezone
from secrets import token_hex
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.doctor_availability import DoctorAvailability
from app.models.user import User
from app.schemas.appointments import AppointmentCreate, AppointmentResponse

router = APIRouter(prefix="/appointments", tags=["Appointments"])

ACTIVE_STATUSES = ("confirmed", "pending")


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Appointment:
    if payload.starts_at.tzinfo is None:
        raise HTTPException(status_code=400, detail="starts_at must include a timezone")

    starts_at = payload.starts_at.astimezone(timezone.utc)
    doctor = db.get(Doctor, payload.doctor_id)
    if doctor is None or doctor.profile_status != "verified":
        raise HTTPException(status_code=404, detail="Doctor not found")

    if starts_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Appointment time must be in the future")

    rules = db.scalars(
        select(DoctorAvailability).where(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.is_active.is_(True),
        )
    ).all()

    matching_rule = None
    ends_at = None

    for rule in rules:
        zone = ZoneInfo(rule.timezone)
        local_start = starts_at.astimezone(zone)
        local_end = local_start + timedelta(minutes=rule.slot_minutes)
        start_minutes = local_start.hour * 60 + local_start.minute
        rule_start_minutes = rule.start_time.hour * 60 + rule.start_time.minute

        if (
            local_start.weekday() == rule.weekday
            and local_start.second == 0
            and local_start.microsecond == 0
            and local_start.time() >= rule.start_time
            and local_end.time() <= rule.end_time
            and (start_minutes - rule_start_minutes) >= 0
            and (start_minutes - rule_start_minutes) % rule.slot_minutes == 0
        ):
            matching_rule = rule
            ends_at = local_end.astimezone(timezone.utc)
            break

    if matching_rule is None or ends_at is None:
        raise HTTPException(status_code=409, detail="The selected time is not an available slot")

    existing = db.scalar(
        select(Appointment).where(
            Appointment.doctor_id == doctor.id,
            Appointment.starts_at == starts_at,
            Appointment.status.in_(ACTIVE_STATUSES),
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="This slot has already been booked")

    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=current_user.id,
        starts_at=starts_at,
        ends_at=ends_at,
        status="confirmed",
        reason=payload.reason,
        booking_reference=f"HH-{token_hex(6).upper()}",
    )
    db.add(appointment)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This slot has already been booked") from exc

    db.refresh(appointment)
    return appointment


@router.get("", response_model=list[AppointmentResponse])
def list_my_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Appointment]:
    return list(
        db.scalars(
            select(Appointment)
            .where(Appointment.patient_id == current_user.id)
            .order_by(Appointment.starts_at.desc())
        ).all()
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_my_appointment(
    appointment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None or appointment.patient_id != current_user.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment
