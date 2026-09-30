from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models.doctor import Doctor
from app.schemas.doctors import DoctorPublicResponse

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("")
def search_doctors(
    q: str | None = Query(default=None, max_length=160),
    specialty: str | None = Query(default=None, max_length=120),
    location: str | None = Query(default=None, max_length=180),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search verified doctor profiles only."""
    filters = [Doctor.profile_status == "verified"]
    if q and q.strip():
        term = f"%{q.strip()}%"
        filters.append(or_(Doctor.full_name.ilike(term), Doctor.specialty.ilike(term)))
    if specialty and specialty.strip():
        filters.append(Doctor.specialty.ilike(f"%{specialty.strip()}%"))
    if location and location.strip():
        filters.append(Doctor.hospital_name.ilike(f"%{location.strip()}%"))

    total = db.scalar(select(func.count()).select_from(Doctor).where(*filters)) or 0
    doctors = db.scalars(
        select(Doctor)
        .options(selectinload(Doctor.credentials))
        .where(*filters)
        .order_by(Doctor.full_name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    return {
        "items": [DoctorPublicResponse.model_validate(item).model_dump(mode="json") for item in doctors],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/{doctor_id}", response_model=DoctorPublicResponse)
def get_doctor(doctor_id: UUID, db: Session = Depends(get_db)):
    doctor = db.scalar(
        select(Doctor)
        .options(selectinload(Doctor.credentials))
        .where(Doctor.id == doctor_id, Doctor.profile_status == "verified")
    )
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor
