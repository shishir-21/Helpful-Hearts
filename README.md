# Helpful Hearts

Helpful Hearts is a planned doctor discovery, appointment booking, and AI-assisted health information platform. It will be developed incrementally with a modular FastAPI backend and a Docker-based local environment.

> Project status: Planning/documentation foundation. Features described here are planned, not implemented, until delivered and tested.

## Product
- **Find Doctors:** Search by name, specialty, and location; view profiles with qualifications, experience, affiliations, contact/booking information, and source-attributed ratings where available.
- **Appointment Booking:** View doctor availability, book appointments, and manage bookings with server-side validation and protection against double booking.
- **AI Health Assistant:** Ask general health questions and receive plain-language information, precautions, and broad lifestyle guidance.
- **Prescription Analyzer:** Upload a prescription, review OCR-extracted text, and receive a clearly labeled explanation of identified medicines, common purposes, side effects, and precautions.

AI features are informational. They are not a diagnosis or a substitute for a licensed clinician, and the application must not autonomously prescribe or recommend medication changes.

## Planned technology stack

| Area | Technology |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Validation | Pydantic |
| Authentication | JWT |
| Containers | Docker, Docker Compose |
| Testing | Pytest, HTTPX |
| AI / OCR | Provider adapters; provider selection pending |

## Project documentation
- [Product requirements](REQUIREMENTS.md) — roles, features, safety, privacy, acceptance criteria, and open decisions.
- [System architecture](ARCHITECTURE.md) — components, backend structure, booking concurrency, data model, integrations, and deployment shape.
- [Development plan](DEVELOPMENT_PLAN.md) — phased roadmap, deliverables, exit criteria, and progress tracker.

## Development approach
Work phase by phase. Keep each phase runnable, add tests alongside features, use small commits, and update documentation as decisions are made. Begin with documentation and the project skeleton before implementing product features.

## Local development
Exact commands will be documented when the frontend/backend scaffold and Compose configuration are added. The intended workflow uses Docker Compose for PostgreSQL and optionally the application services. Do not assume these services are already implemented.

## Configuration and secrets
- Use .env.example as the safe configuration template once added.
- Never commit .env files, API keys, passwords, tokens, private prescriptions, or real patient data.
- Keep development and production configuration separate.

## Data quality and trust
Doctor profiles, credentials, affiliations, contact information, and ratings must have clear provenance and verification status. Demo data must be visibly labeled. Third-party data may only be used when its terms permit it.

## Medical safety and privacy
Health and prescription features require clear uncertainty labels, data minimization, private file storage, access control, and documented retention/deletion rules. Before production use with real patient data, review applicable legal, privacy, and healthcare requirements for the launch jurisdiction.

## License
To be decided before public release.
