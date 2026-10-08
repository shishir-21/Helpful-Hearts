from datetime import datetime, timezone
from pathlib import PurePath
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.schemas.medical_records import (
    MedicalRecordCompleteRequest,
    MedicalRecordCreate,
    MedicalRecordResponse,
    MedicalRecordUploadRequest,
    MedicalRecordUploadResponse,
)
from app.storage.s3 import S3Storage, get_storage

router = APIRouter(prefix="/medical-records", tags=["Medical Records"])


def _get_owned_record(record_id: UUID, user: User, db: Session) -> MedicalRecord:
    record = db.get(MedicalRecord, record_id)
    if record is None or record.patient_id != user.id:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return record


def _validate_upload(payload: MedicalRecordUploadRequest) -> None:
    if payload.mime_type not in settings.medical_record_allowed_mime_types:
        raise HTTPException(status_code=415, detail="Unsupported medical record file type")
    if PurePath(payload.file_name).suffix.lower() not in {".pdf", ".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=415, detail="Unsupported medical record file extension")


@router.get("", response_model=list[MedicalRecordResponse])
def list_medical_records(current_user: User = Depends(get_current_user), category: str | None = Query(default=None, max_length=40), db: Session = Depends(get_db)) -> list[MedicalRecord]:
    query = select(MedicalRecord).where(MedicalRecord.patient_id == current_user.id)
    if category:
        query = query.where(MedicalRecord.category == category)
    return list(db.scalars(query.order_by(MedicalRecord.created_at.desc())).all())


@router.post("", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(payload: MedicalRecordCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MedicalRecord:
    record = MedicalRecord(patient_id=current_user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/upload-url", response_model=MedicalRecordUploadResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record_upload_url(payload: MedicalRecordUploadRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), storage: S3Storage = Depends(get_storage)) -> MedicalRecordUploadResponse:
    _validate_upload(payload)
    record_id = uuid4()
    safe_name = PurePath(payload.file_name).name
    storage_key = f"medical-records/{current_user.id}/{record_id}/{safe_name}"
    record = MedicalRecord(id=record_id, patient_id=current_user.id, title=payload.title, category=payload.category, file_name=safe_name, mime_type=payload.mime_type, storage_key=storage_key)
    db.add(record)
    db.commit()
    try:
        upload_url = storage.create_upload_url(storage_key, payload.mime_type)
    except Exception:
        db.delete(record)
        db.commit()
        raise
    return MedicalRecordUploadResponse(record_id=record.id, upload_url=upload_url, storage_key=storage_key, expires_in=settings.s3_presigned_url_expire_seconds)


@router.post("/{record_id}/complete", response_model=MedicalRecordResponse)
def complete_medical_record_upload(record_id: UUID, _: MedicalRecordCompleteRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), storage: S3Storage = Depends(get_storage)) -> MedicalRecord:
    record = _get_owned_record(record_id, current_user, db)
    if not record.storage_key:
        raise HTTPException(status_code=400, detail="Medical record has no uploaded file")
    metadata = storage.head(record.storage_key)
    size = metadata.get("ContentLength", 0)
    if size <= 0 or size > settings.medical_record_max_bytes:
        storage.delete(record.storage_key)
        db.delete(record)
        db.commit()
        raise HTTPException(status_code=413, detail="Medical record file size is invalid")
    content_type = metadata.get("ContentType")
    if content_type and content_type != record.mime_type:
        storage.delete(record.storage_key)
        db.delete(record)
        db.commit()
        raise HTTPException(status_code=415, detail="Uploaded file type does not match metadata")
    record.file_size = size
    record.upload_completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{record_id}", response_model=MedicalRecordResponse)
def get_medical_record(record_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MedicalRecord:
    return _get_owned_record(record_id, current_user, db)
