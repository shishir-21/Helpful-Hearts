# Helpful Hearts — System Architecture

Status: Proposed | Version: 0.1.0  
Backend: Python + FastAPI | Database: PostgreSQL | Containers: Docker Compose

## 1. Architecture goals
- Keep the initial system simple and practical to run locally.
- Separate UI, API, business rules, persistence, and external providers.
- Make appointment booking transaction-safe.
- Keep AI/OCR integrations replaceable.
- Apply least-privilege access to patient and prescription data.
- Avoid premature microservices.

## 2. High-level architecture

    Patient / Doctor / Admin Browser
                  |
                  v
          Next.js Frontend
                  |
             HTTPS / JSON
                  |
                  v
           FastAPI Backend
                  |
       +----------+-----------+----------------+
       |          |           |                |
       v          v           v                v
    Auth/Users  Doctors/   Appointments     AI/Prescription
                Hospitals   & Availability   Services
       |          |           |                |
       +----------+-----------+----------------+
                  |
                  v
             SQLAlchemy
                  |
                  v
              PostgreSQL

    External integrations behind adapters:
    LLM provider | OCR provider | Email provider
    Permitted doctor/rating data sources | Private object storage

The first release is a modular monolith: one FastAPI application and one PostgreSQL database. Split services only if a demonstrated operational need emerges.

## 3. Technology decisions

| Layer | Choice | Notes |
|---|---|---|
| Frontend | Next.js, TypeScript, Tailwind CSS | Responsive UI based on supplied reference |
| Backend | FastAPI, Python | REST API and generated OpenAPI |
| Validation | Pydantic | Request/response contracts and settings |
| ORM | SQLAlchemy 2.x | Persistence and transaction boundaries |
| Migrations | Alembic | Version-controlled schema changes |
| Database | PostgreSQL | Relational data and transactional booking |
| Authentication | JWT | Secure password hashing and authorization |
| Tests | Pytest, HTTPX | Unit, integration, and API tests |
| Containers | Docker, Docker Compose | Consistent local environment |
| AI/OCR | Provider adapters | Choose after cost, privacy, and quality evaluation |
| Background jobs | Deferred | Add worker/queue only when slow tasks require it |
| File storage | Private local volume in development; private object storage in production | Prescription files must not be public |

## 4. Target repository layout

    Helpful-Hearts/
    ├── frontend/
    │   ├── app/
    │   ├── components/
    │   ├── features/
    │   │   ├── doctors/
    │   │   ├── appointments/
    │   │   ├── assistant/
    │   │   └── prescriptions/
    │   ├── lib/
    │   ├── hooks/
    │   ├── types/
    │   ├── public/
    │   ├── Dockerfile
    │   └── package.json
    ├── backend/
    │   ├── app/
    │   │   ├── main.py
    │   │   ├── api/v1/
    │   │   ├── core/
    │   │   ├── db/
    │   │   ├── models/
    │   │   ├── schemas/
    │   │   ├── repositories/
    │   │   ├── services/
    │   │   ├── integrations/
    │   │   │   ├── ai/
    │   │   │   ├── ocr/
    │   │   │   ├── email/
    │   │   │   └── doctor_data/
    │   │   ├── modules/
    │   │   │   ├── auth/
    │   │   │   ├── users/
    │   │   │   ├── doctors/
    │   │   │   ├── hospitals/
    │   │   │   ├── availability/
    │   │   │   ├── appointments/
    │   │   │   ├── reviews/
    │   │   │   ├── assistant/
    │   │   │   ├── prescriptions/
    │   │   │   └── admin/
    │   │   └── workers/
    │   ├── alembic/
    │   ├── tests/
    │   ├── pyproject.toml
    │   └── Dockerfile
    ├── docs/
    │   ├── API.md
    │   ├── DATA_MODEL.md
    │   └── decisions/
    ├── docker-compose.yml
    ├── .env.example
    ├── .gitignore
    ├── REQUIREMENTS.md
    ├── ARCHITECTURE.md
    ├── DEVELOPMENT_PLAN.md
    └── README.md

This is the target structure. Create folders and modules only when their implementation phase begins.

## 5. Backend layering
Each feature should use a consistent flow:
1. API/router: HTTP routes, status codes, and dependency wiring.
2. Schema: Pydantic request/response contracts.
3. Service: business rules and orchestration.
4. Repository: database queries and persistence.
5. Model: SQLAlchemy mapping.
6. Integration adapter: boundary to external services.

Keep business logic out of route handlers and frontend code. Appointment service operations own the transaction that checks availability and creates or changes a booking.

## 6. Domain modules
- Auth/Users: registration, login, identity, roles, patient profile.
- Doctors: searchable profiles, qualifications, verification metadata.
- Hospitals: clinic details and affiliations.
- Availability: recurring schedules, exceptions, and slot generation.
- Appointments: booking, status transitions, cancellation, and rescheduling.
- Reviews: source-attributed ratings and moderation.
- Assistant: general health-information conversations and safety handling.
- Prescriptions: private upload, OCR, user verification, and explanation.
- Admin: verification and moderation.
- Integrations: provider clients with timeouts, error mapping, and secrets from settings.

## 7. Booking and concurrency
Booking correctness is a core invariant:
- Store appointment instants in UTC and display them in the clinic's configured timezone.
- Generate candidate slots from doctor schedules and exceptions.
- Treat UI availability as advisory; re-check it inside the booking transaction.
- Use PostgreSQL transactions and a concurrency-safe strategy. For single-capacity fixed slots, use a unique constraint on doctor and slot start. For interval/capacity booking, use an appropriate exclusion constraint or locked capacity row.
- Make booking requests idempotent to prevent duplicate bookings on retries.
- Enforce allowed status transitions in the service layer.
- Cancellation/rescheduling must release or replace capacity atomically.
- Send notifications only after transaction commit; notification failure must not undo booking.
- Test simultaneous booking attempts against PostgreSQL.

Start with fixed-duration, single-capacity slots unless product decisions require otherwise.

## 8. Authentication and authorization
- Hash passwords with a maintained password-hashing library (for example, Argon2id).
- Keep signing keys and provider secrets outside source control.
- Validate JWT signature and expiry, and issuer/audience when configured.
- Apply role-based and object-level authorization to every protected operation.
- Patients can access only their own appointments and prescriptions.
- Doctors can access only appointments/schedules in their verified scope.
- Admin actions require an explicit admin role and should be audited.
- Never trust client-supplied user or doctor IDs as proof of access.

## 9. AI and prescription processing

### AI Health Assistant
- Use a provider interface so the model vendor can change without rewriting domain logic.
- Keep prompts, policy checks, output validation, and provider calls in a dedicated service.
- Set timeouts, rate limits, and usage/cost controls.
- Provide general health information only; do not diagnose or prescribe.
- Minimize personal data sent to providers.
- Use vetted medical references where feasible and show sources when available.
- Provide conservative guidance for potentially urgent symptoms.

### Prescription pipeline

    Authenticated upload
          |
    Validate type/size and authorize owner
          |
    Store privately; create processing record
          |
    OCR extraction + confidence metadata
          |
    Patient reviews/corrects extracted text
          |
    Resolve medicines against trusted reference
          |
    Generate constrained plain-language explanation
          |
    Persist result with source/uncertainty labels
          |
    Display to patient; allow deletion

OCR output is untrusted and may be wrong. Separate literal prescription text, reference facts, and AI interpretation. Never infer a definitive diagnosis or recommend medication changes. Do not log prescription contents.

## 10. Conceptual data model
Core entities:
- User (role, credentials, contact preferences)
- PatientProfile
- DoctorProfile
- DoctorCredential / VerificationRecord
- Hospital
- DoctorHospitalAffiliation (status, dates, source)
- DoctorAvailabilityRule
- AvailabilityException
- Appointment (patient, doctor, clinic, start/end, status, type, reference)
- AppointmentStatusEvent
- Review (source, rating, count, moderation status)
- Conversation / Message
- PrescriptionDocument (owner, storage key, status, retention metadata)
- ExtractedPrescriptionItem (raw text, normalized medicine, instructions, confidence)
- MedicineExplanation (source references, explanation, timestamp)
- AuditEvent
- Notification / DeliveryAttempt

Exact fields, indexes, relationships, constraints, and deletion behavior will be defined in docs/DATA_MODEL.md before migrations.

## 11. API conventions
- Version routes under /api/v1.
- Use JSON for normal requests/responses and multipart upload for documents.
- Use consistent error responses and correct HTTP status codes.
- Validate inputs and paginate list endpoints.
- Use FastAPI-generated OpenAPI documentation.
- Do not expose database models directly as API contracts.
- Do not return private patient data in doctor search/profile responses.

Initial route groups:
- /api/v1/auth
- /api/v1/users
- /api/v1/doctors
- /api/v1/hospitals
- /api/v1/availability
- /api/v1/appointments
- /api/v1/reviews
- /api/v1/assistant
- /api/v1/prescriptions
- /api/v1/admin

## 12. Docker and local development
Planned Compose services:
- frontend: Next.js app.
- backend: FastAPI app.
- db: PostgreSQL with named volume and health check.

Possible later services:
- worker and Redis for background tasks.
- object-storage emulator for integration tests.

Requirements:
- Use .env.example with safe placeholders; never commit .env.
- Add database health checks and wait for healthy DB before backend startup.
- Persist DB data in a named volume.
- Expose only necessary local ports.
- Separate development and production configuration.
- Document build, start, stop, logs, migration, and test commands.

## 13. Observability and error handling
- Structured logs with request/correlation IDs.
- Never log secrets, tokens, prescription images, or unnecessary health information.
- Map external provider failures to safe API errors.
- Add health/readiness endpoints.
- Track booking failures and notification delivery without exposing patient details.
- Add monitoring and metrics during deployment preparation.

## 14. Testing
- Unit tests for validation and domain rules.
- API tests for authentication, roles, and object-level access.
- PostgreSQL integration tests for migrations and booking transactions.
- Concurrency tests proving slots cannot be overbooked.
- Mocked AI/OCR adapter tests, including uncertain and failed responses.
- Upload tests for invalid files, size limits, access control, and deletion.
- Frontend tests for search, profile, booking, and prescription flows.
- End-to-end tests for the critical patient journey.
- Never use real patient data in automated tests.

## 15. Deployment
- Frontend and backend may deploy separately.
- Use managed PostgreSQL or a secured database deployment.
- Store secrets in the host's secret manager.
- Use private object storage for prescription files.
- Configure backups, migrations, monitoring, TLS, rate limits, and recovery.
- Complete security, privacy, data-source-permission, and jurisdiction review before handling real patient data.

## 16. Decisions to confirm
1. Launch jurisdiction and applicable compliance requirements.
2. Doctor data and verification sources.
3. Permitted ratings source and access method.
4. AI/OCR providers, data terms, and budget.
5. Auto-confirmation versus approval policy.
6. Slot duration, capacity, and booking horizon.
7. Online consultation and payment scope.
8. Prescription retention and deletion policy.
