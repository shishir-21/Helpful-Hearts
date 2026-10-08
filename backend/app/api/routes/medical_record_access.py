from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_doctor, get_current_user, get_db
from app.models.doctor import Doctor
from app.models.medical_record import MedicalRecord
from app.models.medical_record_access import MedicalRecordAccess
from app.models.user import User
from app.schemas.medical_record_access import MedicalRecordAccessRequest, MedicalRecordAccessResponse
from app.schemas.medical_records import MedicalRecordResponse

router = APIRouter(prefix="/medical-records", tags=["Medical Record Access"])


@router.post("/{record_id}/access", response_model=MedicalRecordAccessResponse, status_code=status.HTTP_201_CREATED)
def grant_medical_record_access(
    record_id: UUID,
    payload: MedicalRecordAccessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicalRecordAccess:
    record = db.get(MedicalRecord, record_id)
    if record is None or record.patient_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medical record not found")
    doctor = db.get(Doctor, payload.doctor_id)
    if doctor is None or doctor.user_id is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    access = MedicalRecordAccess(medical_record_id=record.id, doctor_id=doctor.id, granted_by=current_user.id)
    db.add(access)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Doctor already has access to this record") from exc
    db.refresh(access)
    return access


@router.delete("/{record_id}/access/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_medical_record_access(
    record_id: UUID,
    doctor_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    record = db.get(MedicalRecord, record_id)
    if record is None or record.patient_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medical record not found")
    access = db.scalar(select(MedicalRecordAccess).where(MedicalRecordAccess.medical_record_id == record_id, MedicalRecordAccess.doctor_id == doctor_id))
    if access is None:
        raise HTTPException(status_code=404, detail="Doctor access not found")
    db.delete(access)
    db.commit()


@router.get("/shared-with-me", response_model=list[MedicalRecordResponse])
def list_shared_medical_records(
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> list[MedicalRecord]:
    query = select(MedicalRecord).join(MedicalRecordAccess, MedicalRecordAccess.medical_record_id == MedicalRecord.id).where(MedicalRecordAccess.doctor_id == current_doctor.id).order_by(MedicalRecord.created_at.desc())
    return list(db.scalars(query).all())


@router.get("/{record_id}/shared", response_model=MedicalRecordResponse)
def get_shared_medical_record(
    record_id: UUID,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> MedicalRecord:
    query = select(MedicalRecord).join(MedicalRecordAccess, MedicalRecordAccess.medical_record_id == MedicalRecord.id).where(MedicalRecord.id == record_id, MedicalRecordAccess.doctor_id == current_doctor.id)
    record = db.scalar(query)
    if record is None:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return record
