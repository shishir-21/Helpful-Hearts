from datetime import datetime, timedelta, timezone
from secrets import token_hex
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_doctor, get_current_user, get_db
from app.models.appointment import Appointment
from app.models.appointment_status_history import AppointmentStatusHistory
from app.models.doctor import Doctor
from app.models.doctor_availability import DoctorAvailability
from app.models.user import User
from app.schemas.appointments import (
    AppointmentCancellation,
    AppointmentCreate,
    AppointmentDoctorStatusUpdate,
    AppointmentReschedule,
    AppointmentResponse,
    AppointmentStatusHistoryResponse,
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])
ACTIVE_STATUSES = ("confirmed", "pending")
CANCELLATION_CUTOFF = timedelta(hours=12)


def _get_owned_appointment(appointment_id: UUID, current_user: User, db: Session) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None or appointment.patient_id != current_user.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


def _slot_end(doctor_id: UUID, starts_at: datetime, db: Session) -> datetime:
    rules = db.scalars(
        select(DoctorAvailability).where(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.is_active.is_(True),
        )
    ).all()
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
            and start_minutes >= rule_start_minutes
            and (start_minutes - rule_start_minutes) % rule.slot_minutes == 0
        ):
            return local_end.astimezone(timezone.utc)
    raise HTTPException(status_code=409, detail="The selected time is not an available slot")


def _record_history(
    db: Session,
    appointment: Appointment,
    previous_status: str | None,
    new_status: str,
    event: str,
    note: str | None = None,
    changed_by_user_id: UUID | None = None,
) -> None:
    db.add(
        AppointmentStatusHistory(
            appointment_id=appointment.id,
            changed_by_user_id=changed_by_user_id or appointment.patient_id,
            previous_status=previous_status,
            new_status=new_status,
            event=event,
            note=note,
        )
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _same_idempotent_request(
    appointment: Appointment,
    current_user: User,
    doctor_id: UUID,
    starts_at: datetime,
    reason: str | None,
) -> bool:
    return (
        appointment.patient_id == current_user.id
        and appointment.doctor_id == doctor_id
        and _utc(appointment.starts_at) == starts_at
        and appointment.reason == reason
    )


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> Appointment:
    if payload.starts_at.tzinfo is None:
        raise HTTPException(status_code=400, detail="starts_at must include a timezone")
    starts_at = payload.starts_at.astimezone(timezone.utc)

    if idempotency_key is not None:
        idempotency_key = idempotency_key.strip()
        if not idempotency_key:
            raise HTTPException(status_code=400, detail="Idempotency-Key cannot be empty")
        if len(idempotency_key) > 128:
            raise HTTPException(status_code=400, detail="Idempotency-Key is too long")

        existing = db.scalar(
            select(Appointment).where(Appointment.idempotency_key == idempotency_key)
        )
        if existing is not None:
            if not _same_idempotent_request(
                existing, current_user, payload.doctor_id, starts_at, payload.reason
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency-Key was already used for a different booking request",
                )
            response.status_code = status.HTTP_200_OK
            return existing

    doctor = db.get(Doctor, payload.doctor_id)
    if doctor is None or doctor.profile_status != "verified":
        raise HTTPException(status_code=404, detail="Doctor not found")
    if starts_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Appointment time must be in the future")
    ends_at = _slot_end(doctor.id, starts_at, db)
    overlap = db.scalar(
        select(Appointment).where(
            Appointment.doctor_id == doctor.id,
            Appointment.status.in_(ACTIVE_STATUSES),
            Appointment.starts_at < ends_at,
            Appointment.ends_at > starts_at,
        )
    )
    if overlap is not None:
        raise HTTPException(status_code=409, detail="This slot has already been booked")

    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=current_user.id,
        starts_at=starts_at,
        ends_at=ends_at,
        status="confirmed",
        reason=payload.reason,
        booking_reference=f"HH-{token_hex(6).upper()}",
        idempotency_key=idempotency_key,
    )
    db.add(appointment)
    try:
        db.flush()
        _record_history(db, appointment, None, "confirmed", "booked")
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if idempotency_key is not None:
            existing = db.scalar(
                select(Appointment).where(Appointment.idempotency_key == idempotency_key)
            )
            if existing is not None:
                if not _same_idempotent_request(
                    existing, current_user, payload.doctor_id, starts_at, payload.reason
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="Idempotency-Key was already used for a different booking request",
                    ) from exc
                response.status_code = status.HTTP_200_OK
                return existing
        raise HTTPException(status_code=409, detail="This slot has already been booked") from exc
    db.refresh(appointment)
    return appointment




def _get_doctor_appointment(appointment_id: UUID, doctor: Doctor, db: Session) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None or appointment.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.get("/doctor", response_model=list[AppointmentResponse])
def list_doctor_appointments(
    current_doctor: Doctor = Depends(get_current_doctor),
    appointment_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[Appointment]:
    query = select(Appointment).where(Appointment.doctor_id == current_doctor.id)
    if appointment_status is not None:
        if appointment_status not in {"confirmed", "pending", "completed", "cancelled", "no_show"}:
            raise HTTPException(status_code=400, detail="Invalid appointment status")
        query = query.where(Appointment.status == appointment_status)
    return list(db.scalars(query.order_by(Appointment.starts_at.asc())).all())


@router.get("/doctor/{appointment_id}", response_model=AppointmentResponse)
def get_doctor_appointment(
    appointment_id: UUID,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> Appointment:
    return _get_doctor_appointment(appointment_id, current_doctor, db)


@router.get("/doctor/{appointment_id}/history", response_model=list[AppointmentStatusHistoryResponse])
def get_doctor_appointment_history(
    appointment_id: UUID,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> list[AppointmentStatusHistory]:
    _get_doctor_appointment(appointment_id, current_doctor, db)
    return list(
        db.scalars(
            select(AppointmentStatusHistory)
            .where(AppointmentStatusHistory.appointment_id == appointment_id)
            .order_by(AppointmentStatusHistory.created_at.asc())
        ).all()
    )


@router.patch("/doctor/{appointment_id}/status", response_model=AppointmentResponse)
def update_doctor_appointment_status(
    appointment_id: UUID,
    payload: AppointmentDoctorStatusUpdate,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> Appointment:
    appointment = _get_doctor_appointment(appointment_id, current_doctor, db)
    if appointment.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=409, detail="Only active appointments can be updated")

    now = datetime.now(timezone.utc)
    starts_at = _utc(appointment.starts_at)
    if payload.status in {"completed", "no_show"} and starts_at > now:
        raise HTTPException(
            status_code=409,
            detail=f"Appointments can only be marked {payload.status} after their start time",
        )

    previous = appointment.status
    appointment.status = payload.status
    _record_history(
        db,
        appointment,
        previous,
        payload.status,
        payload.status,
        payload.note,
        changed_by_user_id=current_doctor.user_id,
    )
    db.commit()
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
    return _get_owned_appointment(appointment_id, current_user, db)


@router.get("/{appointment_id}/history", response_model=list[AppointmentStatusHistoryResponse])
def get_appointment_history(
    appointment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AppointmentStatusHistory]:
    _get_owned_appointment(appointment_id, current_user, db)
    return list(
        db.scalars(
            select(AppointmentStatusHistory)
            .where(AppointmentStatusHistory.appointment_id == appointment_id)
            .order_by(AppointmentStatusHistory.created_at.asc())
        ).all()
    )


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: UUID,
    payload: AppointmentCancellation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Appointment:
    appointment = _get_owned_appointment(appointment_id, current_user, db)
    now = datetime.now(timezone.utc)
    starts_at = appointment.starts_at
    if starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=timezone.utc)
    if appointment.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=409, detail="Only active appointments can be cancelled")
    if starts_at - now < CANCELLATION_CUTOFF:
        raise HTTPException(
            status_code=409,
            detail="Appointments can only be cancelled at least 12 hours before they start",
        )
    previous = appointment.status
    appointment.status = "cancelled"
    _record_history(db, appointment, previous, "cancelled", "cancelled", payload.reason)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    appointment_id: UUID,
    payload: AppointmentReschedule,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Appointment:
    appointment = _get_owned_appointment(appointment_id, current_user, db)
    now = datetime.now(timezone.utc)
    old_start = appointment.starts_at
    if old_start.tzinfo is None:
        old_start = old_start.replace(tzinfo=timezone.utc)
    if appointment.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=409, detail="Only active appointments can be rescheduled")
    if old_start - now < CANCELLATION_CUTOFF:
        raise HTTPException(
            status_code=409,
            detail="Appointments can only be rescheduled at least 12 hours before they start",
        )
    if payload.starts_at.tzinfo is None:
        raise HTTPException(status_code=400, detail="starts_at must include a timezone")
    new_start = payload.starts_at.astimezone(timezone.utc)
    if new_start <= now:
        raise HTTPException(status_code=400, detail="Appointment time must be in the future")
    if new_start == old_start:
        raise HTTPException(status_code=400, detail="Choose a different appointment slot")
    new_end = _slot_end(appointment.doctor_id, new_start, db)
    overlap = db.scalar(
        select(Appointment).where(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.id != appointment.id,
            Appointment.status.in_(ACTIVE_STATUSES),
            Appointment.starts_at < new_end,
            Appointment.ends_at > new_start,
        )
    )
    if overlap is not None:
        raise HTTPException(status_code=409, detail="The selected slot has already been booked")
    previous = appointment.status
    appointment.starts_at = new_start
    appointment.ends_at = new_end
    _record_history(
        db,
        appointment,
        previous,
        previous,
        "rescheduled",
        f"Moved from {old_start.isoformat()} to {new_start.isoformat()}",
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="The selected slot has already been booked") from exc
    db.refresh(appointment)
    return appointment
