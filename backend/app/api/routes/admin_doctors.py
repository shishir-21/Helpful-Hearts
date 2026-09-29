from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_roles
from app.models.doctor import Doctor
from app.models.doctor_credential import DoctorCredential
from app.models.user import User
from app.schemas.doctors import CredentialCreate, DoctorAdminResponse, DoctorCreate

router = APIRouter(prefix="/admin", tags=["Admin - Doctor Data"])


def _doctor_or_404(db: Session, doctor_id: UUID) -> Doctor:
    doctor = db.scalar(
        select(Doctor)
        .options(selectinload(Doctor.credentials))
        .where(Doctor.id == doctor_id)
    )
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.post("/doctors", response_model=DoctorAdminResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreate, _admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.commit()
    return _doctor_or_404(db, doctor.id)


@router.get("/doctors", response_model=list[DoctorAdminResponse])
def list_doctors(_admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    doctors = db.scalars(
        select(Doctor)
        .options(selectinload(Doctor.credentials))
        .order_by(Doctor.full_name)
    ).all()
    return list(doctors)


@router.post("/doctors/{doctor_id}/credentials", response_model=DoctorAdminResponse, status_code=status.HTTP_201_CREATED)
def add_credential(
    doctor_id: UUID,
    payload: CredentialCreate,
    _admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if db.get(Doctor, doctor_id) is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    db.add(DoctorCredential(doctor_id=doctor_id, **payload.model_dump()))
    db.commit()
    return _doctor_or_404(db, doctor_id)


@router.patch("/doctors/{doctor_id}/verification", response_model=DoctorAdminResponse)
def verify_doctor(
    doctor_id: UUID,
    verification_status: Literal["draft", "submitted", "verified", "rejected"] = Query(),
    _admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.profile_status = verification_status
    db.commit()
    return _doctor_or_404(db, doctor_id)


@router.patch("/credentials/{credential_id}/verification", response_model=DoctorAdminResponse)
def verify_credential(
    credential_id: UUID,
    verification_status: Literal["unverified", "pending", "verified", "rejected"] = Query(),
    note: str | None = Query(default=None, max_length=3000),
    _admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    credential = db.get(DoctorCredential, credential_id)
    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")
    credential.verification_status = verification_status
    credential.verification_note = note
    credential.verified_at = datetime.now(timezone.utc) if verification_status == "verified" else None
    db.commit()
    return _doctor_or_404(db, credential.doctor_id)
