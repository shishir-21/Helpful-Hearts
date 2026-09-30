from datetime import datetime, timedelta, timezone
from uuid import UUID
from secrets import token_hex

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


def _is_slot_configured(db: Session, doctor_id: UUID, starts_at: datetime, ends_at: datetime) -> bool:
    local_start = starts_at
    local_end = ends_at
    rules = db.scalars(
        select(DoctorAvailability).where(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.is_active.is_(True),
            DoctorAvailability.weekday == local_start.weekday(),
        )
    ).all()
    return any(
        rule.start_time <= local_start.timetz().replace(tzinfo=None)
        and rule.end_time >= local_end.timetz().replace(tzinfo=None)
        and (ends_at - starts_at) == timedelta(minutes=rule.slot_minutes)
        for rule in rules
    )


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
    for rule in rules:
        zone = __import__("zoneinfo").zoneinfo.ZoneInfo(rule.timezone)
        local_start = starts_at.astimezone(zone)
        local_end = local_start + timedelta(minutes=rule.slot_minutes)
        if (
            local_start.weekday() == rule.weekday
            and local_start.time() >= rule.start_time
            and local_end.time() <= rule.end_time
            and local_end > local_start
            and local_start.time().minute % rule.slot_minutes == rule.start_time.minute % rule.slot_minutes
        ):
            matching_rule = rule
            break

    if matching_rule is None:
        raise HTTPException(status_code=409, detail="The selected time is not an available slot")

    ends_at = starts_at + timedelta(minutes=matching_rule.slot_minutes)

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
