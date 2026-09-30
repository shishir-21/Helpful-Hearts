"""Seed a clearly fictional, bookable doctor for local testing.

Run with: docker compose exec backend python -m app.seed_demo
"""
from datetime import time
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.doctor import Doctor
from app.models.doctor_credential import DoctorCredential
from app.models.doctor_availability import DoctorAvailability

DEMO_SOURCE = "Helpful Hearts fictional demo dataset"

def seed_demo_data() -> None:
    with SessionLocal.begin() as db:
        doctor = db.scalar(select(Doctor).where(Doctor.full_name == "Dr. Asha Example"))
        if doctor is None:
            doctor = Doctor(full_name="Dr. Asha Example", specialty="General Medicine", hospital_name="Demo Community Hospital", biography="Fictional profile for local development and booking-flow testing. This is not a real clinician.", years_experience=8, languages="English, Hindi", booking_instructions="Fictional demo profile. Use only for local testing.", profile_status="verified", is_demo=True, source_name=DEMO_SOURCE)
            db.add(doctor)
            db.flush()
        else:
            doctor.profile_status = "verified"
            doctor.is_demo = True
            doctor.booking_instructions = "Fictional demo profile. Use only for local testing."
        credential = db.scalar(select(DoctorCredential).where(DoctorCredential.doctor_id == doctor.id, DoctorCredential.degree == "MBBS (Demo)"))
        if credential is None:
            db.add(DoctorCredential(doctor_id=doctor.id, degree="MBBS (Demo)", institution="Example Medical College (Fictional)", verification_status="unverified", source_name=DEMO_SOURCE))
        rule = db.scalar(select(DoctorAvailability).where(DoctorAvailability.doctor_id == doctor.id, DoctorAvailability.weekday == 0, DoctorAvailability.start_time == time(9,0), DoctorAvailability.end_time == time(12,0), DoctorAvailability.timezone == "Asia/Kolkata"))
        if rule is None:
            db.add(DoctorAvailability(doctor_id=doctor.id, weekday=0, start_time=time(9,0), end_time=time(12,0), slot_minutes=30, timezone="Asia/Kolkata", is_active=True))
        else:
            rule.is_active = True

if __name__ == "__main__":
    seed_demo_data()
    print("Fictional bookable Helpful Hearts demo doctor is ready.")
