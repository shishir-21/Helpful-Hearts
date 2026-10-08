from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.schemas.medical_records import MedicalRecordCreate, MedicalRecordResponse

router = APIRouter(prefix="/medical-records", tags=["Medical Records"])


def _get_owned_record(record_id: UUID, user: User, db: Session) -> MedicalRecord:
    record = db.get(MedicalRecord, record_id)
    if record is None or record.patient_id != user.id:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return record


@router.get("", response_model=list[MedicalRecordResponse])
def list_medical_records(
    current_user: User = Depends(get_current_user),
    category: str | None = Query(default=None, max_length=40),
    db: Session = Depends(get_db),
) -> list[MedicalRecord]:
    query = select(MedicalRecord).where(MedicalRecord.patient_id == current_user.id)
    if category:
        query = query.where(MedicalRecord.category == category)
    return list(db.scalars(query.order_by(MedicalRecord.created_at.desc())).all())


@router.post("", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(
    payload: MedicalRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicalRecord:
    record = MedicalRecord(patient_id=current_user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{record_id}", response_model=MedicalRecordResponse)
def get_medical_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicalRecord:
    return _get_owned_record(record_id, current_user, db)
