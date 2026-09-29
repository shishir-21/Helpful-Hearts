"""Seed a clearly fictional demo doctor.

Run with: python -m app.seed_demo
"""
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.doctor import Doctor
from app.models.doctor_credential import DoctorCredential

DEMO_SOURCE = "Helpful Hearts fictional demo dataset"


def seed_demo_data() -> None:
    with SessionLocal.begin() as db:
        doctor = db.scalar(select(Doctor).where(Doctor.full_name == "Dr. Asha Example"))
        if doctor is None:
            doctor = Doctor(
                full_name="Dr. Asha Example",
                specialty="General Medicine",
                hospital_name="Demo Community Hospital",
                biography="Fictional profile for local development and API testing.",
                years_experience=8,
                languages="English, Hindi",
                booking_instructions="Demo profile only. Appointment booking is not enabled.",
                profile_status="draft",
                is_demo=True,
                source_name=DEMO_SOURCE,
            )
            db.add(doctor)
            db.flush()

        credential = db.scalar(
            select(DoctorCredential).where(
                DoctorCredential.doctor_id == doctor.id,
                DoctorCredential.degree == "MBBS (Demo)",
            )
        )
        if credential is None:
            db.add(
                DoctorCredential(
                    doctor_id=doctor.id,
                    degree="MBBS (Demo)",
                    institution="Example Medical College (Fictional)",
                    verification_status="unverified",
                    source_name=DEMO_SOURCE,
                )
            )


if __name__ == "__main__":
    seed_demo_data()
    print("Fictional Helpful Hearts demo doctor is ready.")
