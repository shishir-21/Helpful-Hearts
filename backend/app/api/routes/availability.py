from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.doctor import Doctor
from app.models.doctor_availability import DoctorAvailability
from app.models.user import User
from app.schemas.availability import AvailabilityCreate, AvailabilityResponse, SlotResponse

router = APIRouter(tags=["Doctor Availability"])


@router.post("/admin/doctors/{doctor_id}/availability", response_model=AvailabilityResponse, status_code=status.HTTP_201_CREATED)
def create_availability(doctor_id: UUID, payload: AvailabilityCreate, _admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    rule = DoctorAvailability(doctor_id=doctor_id, **payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/admin/doctors/{doctor_id}/availability", response_model=list[AvailabilityResponse])
def list_availability(doctor_id: UUID, _admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if db.get(Doctor, doctor_id) is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return list(db.scalars(select(DoctorAvailability).where(DoctorAvailability.doctor_id == doctor_id).order_by(DoctorAvailability.weekday, DoctorAvailability.start_time)).all())


@router.delete("/admin/availability/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability(rule_id: UUID, _admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    rule = db.get(DoctorAvailability, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Availability rule not found")
    db.delete(rule)
    db.commit()


@router.get("/doctors/{doctor_id}/availability", response_model=list[SlotResponse])
def get_available_slots(
    doctor_id: UUID,
    from_date: date = Query(default_factory=date.today),
    days: int = Query(default=14, ge=1, le=30),
    db: Session = Depends(get_db),
):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None or doctor.profile_status != "verified":
        raise HTTPException(status_code=404, detail="Doctor not found")
    rules = db.scalars(select(DoctorAvailability).where(DoctorAvailability.doctor_id == doctor_id, DoctorAvailability.is_active.is_(True))).all()
    now = datetime.now(timezone.utc)
    slots = []
    for offset in range(days):
        day = from_date + timedelta(days=offset)
        for rule in rules:
            if rule.weekday != day.weekday():
                continue
            zone = ZoneInfo(rule.timezone)
            start = datetime.combine(day, rule.start_time, tzinfo=zone)
            end = datetime.combine(day, rule.end_time, tzinfo=zone)
            cursor = start
            while cursor + timedelta(minutes=rule.slot_minutes) <= end:
                slot_end = cursor + timedelta(minutes=rule.slot_minutes)
                if cursor.astimezone(timezone.utc) > now:
                    slots.append(SlotResponse(starts_at=cursor.isoformat(), ends_at=slot_end.isoformat(), timezone=rule.timezone))
                cursor = slot_end
    slots.sort(key=lambda item: item.starts_at)
    return slots
