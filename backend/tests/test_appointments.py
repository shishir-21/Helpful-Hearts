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
        test_client.testing_session = testing_session
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _create_doctor_and_patient(client, doctor_name: str):
    patient = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Test Patient", password_hash="unused")
    doctor = Doctor(
        id=uuid4(),
        full_name=doctor_name,
        specialty="General Medicine",
        profile_status="verified",
        is_demo=True,
        source_name="Fictional test data",
    )
    db = next(app.dependency_overrides[get_db]())
    db.add_all([patient, doctor])
    db.commit()
    db.close()
    app.dependency_overrides[get_current_user] = lambda: patient
    return patient, doctor


def test_book_available_slot_and_block_duplicate(client):
    _, doctor = _create_doctor_and_patient(client, "Dr. Booking Example")
    today = date.today()
    monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    from zoneinfo import ZoneInfo

    slot = datetime.combine(monday, time(10, 0), tzinfo=ZoneInfo("Asia/Kolkata"))
    db = next(app.dependency_overrides[get_db]())
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
    _, doctor = _create_doctor_and_patient(client, "Dr. Idempotency Example")
    booking_day = date.today() + timedelta(days=(7 - date.today().weekday()) % 7 or 7)
    slot = datetime.combine(booking_day, time(10, 0), tzinfo=timezone.utc)

    db = next(app.dependency_overrides[get_db]())
    db.add(
        DoctorAvailability(
            doctor_id=doctor.id,
            weekday=booking_day.weekday(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_minutes=30,
            timezone="UTC",
            is_active=True,
        )
    )
    db.commit()
    db.close()

    payload = {"doctor_id": str(doctor.id), "starts_at": slot.isoformat(), "reason": "Routine consultation"}
    headers = {"Idempotency-Key": "booking-retry-001"}
    first = client.post("/api/v1/appointments", json=payload, headers=headers)
    assert first.status_code == 201

    second = client.post("/api/v1/appointments", json=payload, headers=headers)
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["booking_reference"] == first.json()["booking_reference"]


def test_idempotency_key_cannot_be_reused_for_different_request(client):
    _, doctor = _create_doctor_and_patient(client, "Dr. Idempotency Conflict")
    booking_day = date.today() + timedelta(days=7)
    first_slot = datetime.combine(booking_day, time(9, 0), tzinfo=timezone.utc)
    second_slot = datetime.combine(booking_day, time(9, 30), tzinfo=timezone.utc)

    db = next(app.dependency_overrides[get_db]())
    db.add(
        DoctorAvailability(
            doctor_id=doctor.id,
            weekday=booking_day.weekday(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_minutes=30,
            timezone="UTC",
            is_active=True,
        )
    )
    db.commit()
    db.close()

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
    patient, doctor = _create_doctor_and_patient(client, "Dr. Schedule Example")
    db = next(app.dependency_overrides[get_db]())
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
    doctor = Doctor(
        id=uuid4(),
        full_name="Dr. Cancel Example",
        specialty="General Medicine",
        profile_status="verified",
        is_demo=True,
        source_name="Fictional test data",
    )
    starts = datetime.now(timezone.utc) + timedelta(days=7)
    appointment = Appointment(
        id=uuid4(),
        doctor_id=doctor.id,
        patient_id=patient.id,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=30),
        status="confirmed",
        booking_reference=f"HH-{uuid4().hex[:12].upper()}",
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
    doctor = Doctor(
        id=uuid4(),
        full_name="Dr. Late Cancel",
        specialty="General Medicine",
        profile_status="verified",
        is_demo=True,
        source_name="Fictional test data",
    )
    starts = datetime.now(timezone.utc) + timedelta(hours=6)
    appointment = Appointment(
        id=uuid4(),
        doctor_id=doctor.id,
        patient_id=patient.id,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=30),
        status="confirmed",
        booking_reference=f"HH-{uuid4().hex[:12].upper()}",
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
    doctor = Doctor(
        id=uuid4(),
        full_name="Dr. Reschedule Example",
        specialty="General Medicine",
        profile_status="verified",
        is_demo=True,
        source_name="Fictional test data",
    )
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7 or 7
    first_monday = today + timedelta(days=days_until_monday)
    second_monday = first_monday + timedelta(days=7)
    old_start = datetime.combine(first_monday, time(9, 0), tzinfo=ZoneInfo("Asia/Kolkata"))
    new_start = datetime.combine(second_monday, time(9, 0), tzinfo=ZoneInfo("Asia/Kolkata"))
    appointment = Appointment(
        id=uuid4(),
        doctor_id=doctor.id,
        patient_id=patient.id,
        starts_at=old_start.astimezone(timezone.utc),
        ends_at=(old_start + timedelta(minutes=30)).astimezone(timezone.utc),
        status="confirmed",
        booking_reference=f"HH-{uuid4().hex[:12].upper()}",
    )
    db = next(app.dependency_overrides[get_db]())
    db.add_all([patient, doctor, appointment])
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


def _create_doctor_appointment(client, starts_at: datetime):
    doctor_user = User(
        id=uuid4(),
        email=f"doctor-{uuid4()}@example.com",
        full_name="Doctor Account",
        password_hash="unused",
        role="doctor",
    )
    patient = User(
        id=uuid4(),
        email=f"patient-{uuid4()}@example.com",
        full_name="Appointment Patient",
        password_hash="unused",
        role="patient",
    )
    doctor = Doctor(
        id=uuid4(),
        user_id=doctor_user.id,
        full_name="Dr. Managed Appointments",
        specialty="Cardiology",
        profile_status="verified",
        is_demo=False,
        source_name="Fictional test data",
    )
    appointment = Appointment(
        id=uuid4(),
        doctor_id=doctor.id,
        patient_id=patient.id,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=30),
        status="confirmed",
        booking_reference=f"HH-{uuid4().hex[:12].upper()}",
    )
    db = client.testing_session()
    db.add_all([doctor_user, patient, doctor, appointment])
    db.commit()
    appointment_id = appointment.id
    db.close()
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    return doctor_user, patient, doctor, appointment_id


def test_doctor_only_sees_own_appointments(client):
    _, patient, doctor, own_id = _create_doctor_appointment(
        client, datetime.now(timezone.utc) + timedelta(days=2)
    )
    other_doctor_user = User(
        id=uuid4(),
        email=f"doctor-{uuid4()}@example.com",
        full_name="Other Doctor",
        password_hash="unused",
        role="doctor",
    )
    other_doctor = Doctor(
        id=uuid4(),
        user_id=other_doctor_user.id,
        full_name="Dr. Other",
        specialty="Neurology",
        profile_status="verified",
        is_demo=False,
        source_name="Fictional test data",
    )
    other_appointment = Appointment(
        id=uuid4(),
        doctor_id=other_doctor.id,
        patient_id=patient.id,
        starts_at=datetime.now(timezone.utc) + timedelta(days=3),
        ends_at=datetime.now(timezone.utc) + timedelta(days=3, minutes=30),
        status="confirmed",
        booking_reference=f"HH-{uuid4().hex[:12].upper()}",
    )
    db = client.testing_session()
    db.add_all([other_doctor_user, other_doctor, other_appointment])
    db.commit()
    other_id = other_appointment.id
    db.close()

    response = client.get("/api/v1/appointments/doctor")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [str(own_id)]
    assert client.get(f"/api/v1/appointments/doctor/{own_id}").status_code == 200
    assert client.get(f"/api/v1/appointments/doctor/{other_id}").status_code == 404
    assert doctor.id != other_doctor.id


def test_patient_cannot_access_doctor_appointment_management(client):
    patient = User(
        id=uuid4(),
        email=f"{uuid4()}@example.com",
        full_name="Patient",
        password_hash="unused",
        role="patient",
    )
    db = client.testing_session()
    db.add(patient)
    db.commit()
    db.close()
    app.dependency_overrides[get_current_user] = lambda: patient

    response = client.get("/api/v1/appointments/doctor")
    assert response.status_code == 403


def test_doctor_can_cancel_appointment_and_history_records_doctor(client):
    doctor_user, _, _, appointment_id = _create_doctor_appointment(
        client, datetime.now(timezone.utc) + timedelta(hours=6)
    )

    response = client.patch(
        f"/api/v1/appointments/doctor/{appointment_id}/status",
        json={"status": "cancelled", "note": "Doctor unavailable"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    history = client.get(f"/api/v1/appointments/doctor/{appointment_id}/history")
    assert history.status_code == 200
    assert history.json()[0]["event"] == "cancelled"
    assert history.json()[0]["changed_by_user_id"] == str(doctor_user.id)


def test_doctor_cannot_complete_future_appointment(client):
    _, _, _, appointment_id = _create_doctor_appointment(
        client, datetime.now(timezone.utc) + timedelta(hours=2)
    )

    response = client.patch(
        f"/api/v1/appointments/doctor/{appointment_id}/status",
        json={"status": "completed"},
    )
    assert response.status_code == 409
    assert "after their start time" in response.json()["detail"]


def test_doctor_can_complete_started_appointment(client):
    _, _, _, appointment_id = _create_doctor_appointment(
        client, datetime.now(timezone.utc) - timedelta(minutes=15)
    )

    response = client.patch(
        f"/api/v1/appointments/doctor/{appointment_id}/status",
        json={"status": "completed", "note": "Consultation completed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
