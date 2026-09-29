# Helpful Hearts

Helpful Hearts is a doctor discovery, appointment booking, and AI-assisted health information platform. It is being developed incrementally as a modular FastAPI application with a Next.js frontend and a Docker-based local environment.

> Project status: Phase 1 local runtime verified; Phase 2 authentication implementation is in progress. Product features are considered complete only after their exit checks pass.

## Product
- **Find Doctors:** Search by name, specialty, and location; view profiles with qualifications, experience, affiliations, contact/booking information, and source-attributed ratings where available.
- **Appointment Booking:** View doctor availability, book appointments, and manage bookings with server-side validation and protection against double booking.
- **AI Health Assistant:** Ask general health questions and receive plain-language information, precautions, and broad lifestyle guidance.
- **Prescription Analyzer:** Upload a prescription, review OCR-extracted text, and receive a clearly labeled explanation of identified medicines, common purposes, side effects, and precautions.

AI features are informational. They are not a diagnosis or a substitute for a licensed clinician, and the application must not autonomously prescribe or recommend medication changes.

## Technology stack

| Area | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, Uvicorn |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Validation / settings | Pydantic, pydantic-settings |
| Containers | Docker, Docker Compose |
| Testing | Pytest, HTTPX |
| AI / OCR | Provider adapters; provider selection pending |

## Repository layout

```text
Helpful-Hearts/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── package.json
│   ├── Dockerfile
│   └── ...
├── docker-compose.yml
├── .env.example
├── .gitignore
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── DEVELOPMENT_PLAN.md
└── README.md
```

## Prerequisites
- Git
- Docker Desktop with the Linux container engine running
- Node.js 22 or newer (Node.js 24 is supported by this scaffold)
- Python 3.12 is used inside the backend Docker image. A local Python installation is not required when running the full stack with Compose.

## Local development (Docker Compose)

From the repository root:

1. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Start the application:

   ```powershell
   docker compose up --build
   ```

3. Open:
   - Frontend: http://localhost:3000
   - API root: http://localhost:8000/
   - Liveness: http://localhost:8000/health
   - Database readiness: http://localhost:8000/api/v1/health/ready
   - Interactive API docs: http://localhost:8000/docs

4. Apply database migrations (in another terminal while the stack is running):\n\n   ```powershell\n   docker compose exec backend alembic upgrade head\n   ```\n\n5. Stop the stack:

   ```powershell
   docker compose down
   ```

PostgreSQL data is stored in a named Docker volume and survives container recreation. To remove the database volume as well (destructive; deletes local database data), run `docker compose down -v`.

If port 3000, 5432, or 8000 is already in use, change the corresponding port in `.env`. The values in `.env.example` are local development defaults only.

## Run services outside Docker (optional)

The backend can be run locally with Python 3.12 and a reachable PostgreSQL instance:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The frontend can be run locally in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

When running the backend outside Compose, set `DATABASE_URL` to a local database address (for example, host `localhost`) and configure `FRONTEND_ORIGIN` as needed. The frontend API base URL is `NEXT_PUBLIC_API_URL`.

## Current scaffold behavior
- The frontend displays a simple project landing page.
- FastAPI exposes `/`, `/health`, and `/api/v1/health/ready`.
- The readiness endpoint checks the PostgreSQL connection.
- Doctor search, authentication, booking, AI, and prescription features are not implemented yet.

## Project documentation
- [Product requirements](REQUIREMENTS.md) — roles, features, safety, privacy, acceptance criteria, and open decisions.
- [System architecture](ARCHITECTURE.md) — components, backend structure, booking concurrency, data model, integrations, and deployment shape.
- [Development plan](DEVELOPMENT_PLAN.md) — phased roadmap, deliverables, exit criteria, and progress tracker.

## Development approach
Work phase by phase. Keep each phase runnable, add tests alongside features, use small commits, and update documentation as decisions are made. Use clearly labeled demo data until data sources and permissions are established.

## Configuration and secrets
- Copy `.env.example` to `.env` for local development.
- Never commit `.env` files, API keys, passwords, tokens, private prescriptions, or real patient data.
- Keep development and production configuration separate.

## Data quality and trust
Doctor profiles, credentials, affiliations, contact information, and ratings must have clear provenance and verification status. Demo data must be visibly labeled. Third-party data may only be used when its terms permit it.

## Medical safety and privacy
Health and prescription features require clear uncertainty labels, data minimization, private file storage, access control, and documented retention/deletion rules. Before production use with real patient data, review applicable legal, privacy, and healthcare requirements for the launch jurisdiction.

## License
To be decided before public release.
