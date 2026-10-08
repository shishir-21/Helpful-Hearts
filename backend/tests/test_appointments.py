from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db
from app.db.session import Base
from app.main import app
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.doctor_availability import DoctorAvailability
from app.models.user import User


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_book_available_slot_and_block_duplicate(client):
    patient = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Test Patient", password_hash="unused")
    doctor = Doctor(
        id=uuid4(),
        full_name="Dr. Booking Example",
        specialty="General Medicine",
        profile_status="verified",
        is_demo=True,
        source_name="Fictional test data",
    )
    db = next(app.dependency_overrides[get_db]())
    db.add_all([patient, doctor])
    db.commit()

    import datetime as dt
    today = dt.date.today()
    monday = today + dt.timedelta(days=(7 - today.weekday()) % 7 or 7)
    from zoneinfo import ZoneInfo
    slot = dt.datetime.combine(monday, dt.time(10, 0), tzinfo=ZoneInfo("Asia/Kolkata"))
    db.add(
        DoctorAvailability(
            doctor_id=doctor.id,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_minutes=30,
            timezone="Asia/Kolkata",
            is_active=True,
        )
    )
    db.commit()
    db.close()

    app.dependency_overrides[get_current_user] = lambda: patient

    first = client.post(
        "/api/v1/appointments",
        json={"doctor_id": str(doctor.id), "starts_at": slot.isoformat(), "reason": "Routine consultation"},
    )
    assert first.status_code == 201
    assert first.json()["status"] == "confirmed"
    assert first.json()["booking_reference"].startswith("HH-")

    second = client.post(
        "/api/v1/appointments",
        json={"doctor_id": str(doctor.id), "starts_at": slot.isoformat()},
    )
    assert second.status_code == 409


def test_idempotency_key_returns_same_appointment(client):
    patient = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Idempotent Patient", password_hash="unused")
    doctor = Doctor(
        id=uuid4(),
        full_name="Dr. Idempotency Example",
        specialty="General Medicine",
        profile_status="verified",
        is_demo=True,
        source_name="Fictional test data",
    )
    db = next(app.dependency_overrides[get_db]())
    db.add_all([patient, doctor])
    db.add(
        DoctorAvailability(
            doctor_id=doctor.id,
            weekday=(date.today() + timedelta(days=1)).weekday(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_minutes=30,
            timezone="Asia/Kolkata",
            is_active=True,
        )
    )
    db.commit()
    db.close()
    app.dependency_overrides[get_current_user] = lambda: patient

    future_day = date.today() + timedelta(days=1)
    weekday = future_day.weekday()
    # Move to the next configured weekday if tomorrow is not Monday.
    days_until_monday = (7 - date.today().weekday()) % 7 or 7
    booking_day = date.today() + timedelta(days=days_until_monday)
    slot = datetime.combine(booking_day, time(10, 0), tzinfo=timezone.utc)
    # Configure a Monday slot in the doctor's local timezone.
    slot = datetime.combine(booking_day, time(10, 0), tzinfo=timezone.utc)

    payload = {"doctor_id": str(doctor.id), "starts_at": slot.isoformat(), "reason": "Routine consultation"}
    headers = {"Idempotency-Key": "booking-retry-001"}
    first = client.post("/api/v1/appointments", json=payload, headers=headers)
    assert first.status_code == 201
    second = client.post("/api/v1/appointments", json=payload, headers=headers)
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["booking_reference"] == first.json()["booking_reference"]


def test_idempotency_key_cannot_be_reused_for_different_request(client):
    patient = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Idempotency Conflict", password_hash="unused")
    doctor = Doctor(
        id=uuid4(),
        full_name="Dr. Idempotency Conflict",
        specialty="General Medicine",
        profile_status="verified",
        is_demo=True,
        source_name="Fictional test data",
    )
    db = next(app.dependency_overrides[get_db]())
    db.add_all([patient, doctor])
    db.add(
        DoctorAvailability(
            doctor_id=doctor.id,
            weekday=(date.today() + timedelta(days=7)).weekday(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_minutes=30,
            timezone="UTC",
            is_active=True,
        )
    )
    db.commit()
    db.close()
    app.dependency_overrides[get_current_user] = lambda: patient

    booking_day = date.today() + timedelta(days=7)
    first_slot = datetime.combine(booking_day, time(9, 0), tzinfo=timezone.utc)
    second_slot = datetime.combine(booking_day, time(9, 30), tzinfo=timezone.utc)
    headers = {"Idempotency-Key": "booking-conflict-001"}
    first = client.post(
        "/api/v1/appointments",
        json={"doctor_id": str(doctor.id), "starts_at": first_slot.isoformat()},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/appointments",
        json={"doctor_id": str(doctor.id), "starts_at": second_slot.isoformat()},
        headers=headers,
    )
    assert second.status_code == 409
    assert "different booking request" in second.json()["detail"]


def test_booking_rejects_outside_schedule(client):
    patient = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Test Patient", password_hash="unused")
    doctor = Doctor(
        id=uuid4(),
        full_name="Dr. Schedule Example",
        specialty="Cardiology",
        profile_status="verified",
        is_demo=True,
        source_name="Fictional test data",
    )
    db = next(app.dependency_overrides[get_db]())
    db.add_all([patient, doctor])
    db.add(
        DoctorAvailability(
            doctor_id=doctor.id,
            weekday=date.today().weekday(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_minutes=30,
            timezone="Asia/Kolkata",
            is_active=True,
        )
    )
    db.commit()
    db.close()
    app.dependency_overrides[get_current_user] = lambda: patient

    future = datetime.combine(date.today() + timedelta(days=1), time(20, 0), tzinfo=timezone.utc)
    response = client.post(
        "/api/v1/appointments",
        json={"doctor_id": str(doctor.id), "starts_at": future.isoformat()},
    )
    assert response.status_code == 409


def test_patient_only_sees_own_appointments(client):
    first = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="First Patient", password_hash="unused")
    second = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Second Patient", password_hash="unused")
    doctor = Doctor(
        id=uuid4(),
        full_name="Dr. Ownership Example",
        specialty="Dermatology",
        profile_status="verified",
        is_demo=True,
        source_name="Fictional test data",
    )
    starts = datetime.now(timezone.utc) + timedelta(days=7)
    appointment = Appointment(
        id=uuid4(),
        doctor_id=doctor.id,
        patient_id=first.id,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=30),
        status="confirmed",
        booking_reference=f"HH-{uuid4().hex[:12].upper()}",
    )
    db = next(app.dependency_overrides[get_db]())
    db.add_all([first, second, doctor, appointment])
    db.commit()
    db.close()

    app.dependency_overrides[get_current_user] = lambda: second
    assert client.get(f"/api/v1/appointments/{appointment.id}").status_code == 404

    app.dependency_overrides[get_current_user] = lambda: first
    response = client.get(f"/api/v1/appointments/{appointment.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(appointment.id)


def test_patient_can_cancel_at_least_12_hours_before_and_history_is_recorded(client):
    patient = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Cancel Patient", password_hash="unused")
    doctor = Doctor(id=uuid4(), full_name="Dr. Cancel Example", specialty="General Medicine", profile_status="verified", is_demo=True, source_name="Fictional test data")
    starts = datetime.now(timezone.utc) + timedelta(days=7)
    appointment = Appointment(
        id=uuid4(), doctor_id=doctor.id, patient_id=patient.id,
        starts_at=starts, ends_at=starts + timedelta(minutes=30),
        status="confirmed", booking_reference=f"HH-{uuid4().hex[:12].upper()}",
    )
    db = next(app.dependency_overrides[get_db]())
    db.add_all([patient, doctor, appointment])
    db.commit()
    appointment_id = appointment.id
    db.close()
    app.dependency_overrides[get_current_user] = lambda: patient

    response = client.post(f"/api/v1/appointments/{appointment_id}/cancel", json={"reason": "Plans changed"})
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    history = client.get(f"/api/v1/appointments/{appointment_id}/history")
    assert history.status_code == 200
    assert [event["event"] for event in history.json()] == ["cancelled"]
    assert history.json()[0]["note"] == "Plans changed"


def test_patient_cannot_cancel_within_12_hours(client):
    patient = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Late Cancel Patient", password_hash="unused")
    doctor = Doctor(id=uuid4(), full_name="Dr. Late Cancel", specialty="General Medicine", profile_status="verified", is_demo=True, source_name="Fictional test data")
    starts = datetime.now(timezone.utc) + timedelta(hours=6)
    appointment = Appointment(
        id=uuid4(), doctor_id=doctor.id, patient_id=patient.id,
        starts_at=starts, ends_at=starts + timedelta(minutes=30),
        status="confirmed", booking_reference=f"HH-{uuid4().hex[:12].upper()}",
    )
    db = next(app.dependency_overrides[get_db]())
    db.add_all([patient, doctor, appointment])
    db.commit()
    appointment_id = appointment.id
    db.close()
    app.dependency_overrides[get_current_user] = lambda: patient

    response = client.post(f"/api/v1/appointments/{appointment_id}/cancel", json={"reason": "Too late"})
    assert response.status_code == 409
    assert "12 hours" in response.json()["detail"]


def test_patient_can_reschedule_before_12_hour_cutoff(client):
    from zoneinfo import ZoneInfo

    patient = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Reschedule Patient", password_hash="unused")
    doctor = Doctor(id=uuid4(), full_name="Dr. Reschedule Example", specialty="General Medicine", profile_status="verified", is_demo=True, source_name="Fictional test data")
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7 or 7
    first_monday = today + timedelta(days=days_until_monday)
    second_monday = first_monday + timedelta(days=7)
    old_start = datetime.combine(first_monday, time(9, 0), tzinfo=ZoneInfo("Asia/Kolkata"))
    new_start = datetime.combine(second_monday, time(9, 0), tzinfo=ZoneInfo("Asia/Kolkata"))
    appointment = Appointment(
        id=uuid4(), doctor_id=doctor.id, patient_id=patient.id,
        starts_at=old_start.astimezone(timezone.utc),
        ends_at=(old_start + timedelta(minutes=30)).astimezone(timezone.utc),
        status="confirmed", booking_reference=f"HH-{uuid4().hex[:12].upper()}",
    )
    db = next(app.dependency_overrides[get_db]())
    db.add_all([patient, doctor, appointment])
    db.add(DoctorAvailability(
        doctor_id=doctor.id, weekday=0, start_time=time(9, 0), end_time=time(12, 0),
        slot_minutes=30, timezone="Asia/Kolkata", is_active=True,
    ))
    db.commit()
    appointment_id = appointment.id
    db.close()
    app.dependency_overrides[get_current_user] = lambda: patient

    response = client.post(
        f"/api/v1/appointments/{appointment_id}/reschedule",
        json={"starts_at": new_start.isoformat()},
    )
    assert response.status_code == 200
    returned_start = datetime.fromisoformat(response.json()["starts_at"].replace("Z", "+00:00"))
    if returned_start.tzinfo is None:
        returned_start = returned_start.replace(tzinfo=timezone.utc)
    assert returned_start.astimezone(timezone.utc) == new_start.astimezone(timezone.utc)

    history = client.get(f"/api/v1/appointments/{appointment_id}/history")
    assert history.status_code == 200
    assert history.json()[0]["event"] == "rescheduled"
