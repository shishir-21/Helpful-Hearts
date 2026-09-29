"""Seed clearly fictional demo doctor and hospital records.

Run with: python -m app.seed_demo
"""
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.doctor import Doctor
from app.models.doctor_credential import DoctorCredential
from app.models.doctor_hospital_affiliation import DoctorHospitalAffiliation
from app.models.hospital import Hospital

DEMO_SOURCE = "Helpful Hearts fictional demo dataset"


def seed_demo_data() -> None:
    with SessionLocal.begin() as db:
        hospital = db.scalar(select(Hospital).where(Hospital.name == "Demo Community Hospital"))
        if hospital is None:
            hospital = Hospital(
                name="Demo Community Hospital",
                address="100 Example Road",
                city="Demo City",
                state="Demo State",
                country="India",
                phone=None,
                email=None,
                is_demo=True,
                source_name=DEMO_SOURCE,
            )
            db.add(hospital)
            db.flush()

        doctor = db.scalar(select(Doctor).where(Doctor.full_name == "Dr. Asha Example"))
        if doctor is None:
            doctor = Doctor(
                full_name="Dr. Asha Example",
                specialty="General Medicine",
                biography="Fictional profile for local development and API testing.",
                years_experience=8,
                languages="English, Hindi",
                public_phone=None,
                public_email=None,
                booking_instructions="Demo profile only. Appointment booking is not enabled.",
                registration_number=None,
                registration_council=None,
                registration_state=None,
                registration_year=None,
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

        affiliation = db.scalar(
            select(DoctorHospitalAffiliation).where(
                DoctorHospitalAffiliation.doctor_id == doctor.id,
                DoctorHospitalAffiliation.hospital_id == hospital.id,
            )
        )
        if affiliation is None:
            db.add(
                DoctorHospitalAffiliation(
                    doctor_id=doctor.id,
                    hospital_id=hospital.id,
                    role_title="Demo Consultant",
                    status="current",
                    is_demo=True,
                    source_name=DEMO_SOURCE,
                )
            )


if __name__ == "__main__":
    seed_demo_data()
    print("Fictional Helpful Hearts demo records are ready.")
