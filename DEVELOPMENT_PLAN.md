# Helpful Hearts — Development Plan

Status: Proposed roadmap | Version: 0.1.0  
Method: Incremental delivery, tests with features, small descriptive commits.

## Working rules
1. Build one phase at a time; do not begin the next phase until exit checks pass.
2. Keep the application runnable at each phase boundary.
3. Use small, descriptive commits.
4. Never commit secrets, .env files, real patient data, or unlicensed assets.
5. Use clearly labeled demo data until data sources and permissions are established.
6. Add tests alongside features.
7. Update README, API docs, and this plan as decisions or commands change.
8. Start with a modular monolith; avoid premature microservices.
9. Keep local resource usage low and run only required services.
10. AI must not be presented as diagnosis or autonomous prescribing.

## Phase 0 — Product definition and repository foundation
Deliverables: REQUIREMENTS.md, ARCHITECTURE.md, DEVELOPMENT_PLAN.md, README.md, .gitignore, .env.example.
Tasks:
- Confirm product scope, user roles, MVP, and non-goals.
- Record launch-jurisdiction and compliance questions.
- Define doctor data provenance and verification states.
- Record booking policy decisions to resolve before implementation.
- Commit the documentation foundation.
Exit criteria:
- Documentation committed; no secrets in repository.
- MVP and unresolved decisions are explicit.

## Phase 1 — Project skeleton and local infrastructure
Deliverables: FastAPI skeleton, Next.js skeleton, Dockerfiles, Docker Compose, PostgreSQL volume/health check, environment template, health endpoints.
Tasks:
- Pin supported Python and Node versions.
- Configure backend and frontend dev commands.
- Configure database settings and local CORS.
- Add formatting, linting, and test commands.
- Verify a clean clone can start from documented instructions.
Exit criteria:
- Frontend opens locally; FastAPI health endpoint responds; backend connects to PostgreSQL.
- Compose starts/stops cleanly; no secrets committed.

## Phase 2 — Database and authentication
Deliverables: SQLAlchemy setup, Alembic migrations, user/role models, registration/login/current-user APIs, basic auth UI.
Tasks:
- Establish migration conventions.
- Implement secure password hashing and JWT validation.
- Enforce role checks on the server.
- Add input validation and consistent errors.
- Test duplicate users, invalid credentials, token expiry, and protected routes.
Exit criteria:
- User can register/login; protected routes reject unauthenticated requests.
- Role restrictions tested; migrations work from an empty DB.

## Phase 3 — Doctor profile data foundation
Deliverables: doctor and credential models; optional clinic/hospital name on doctor profile; admin-managed demo data; initial API contracts.
Tasks:
- Define public/private profile fields.
- Store an optional clinic/hospital name directly on the doctor profile.
- Define verification states.
- Seed clearly labeled demo records.
- Add admin-only management and verification endpoints.
Exit criteria:
- Authorized users can manage demo doctor records and credentials.
- Demo/unverified records are not misrepresented as verified.
- No separate hospital management section or API is exposed.

## Phase 4 — Doctor search and profile UI
Deliverables: reference-inspired responsive search page, filters, result cards, profile page, search API.
Tasks:
- Build navigation, search, category chips, doctor cards, profile components.
- Add paginated name/specialty/location search and indexes.
- Display experience, optional clinic/hospital name, source, and verification state.
- Add map only for valid coordinates and keep an accessible list.
- Use demo data until real sources are approved.
Exit criteria:
- Search/filter/profile flow works on desktop and mobile.
- Pagination and loading/empty/error states work.
- No fabricated real-world data.

## Phase 5 — Doctor availability
Deliverables: schedule rules, exceptions, schedule management UI/API, slot generation.
Tasks:
- Decide timezone, duration, buffers, capacity, lead time, booking horizon.
- Support recurring weekly availability and date exceptions.
- Generate future slots while accounting for existing bookings.
- Restrict schedule edits to authorized doctor/staff.
- Test timezone and daylight-saving behavior where relevant.
Exit criteria:
- Authorized users can configure schedules.
- Patient API returns only valid future slots.
- Timezone behavior is documented and tested.

## Phase 6 — Appointment booking core
Deliverables: appointment model/migrations, booking API, slot selection UI, confirmation page, booking reference.
Tasks:
- Finalize automatic confirmation versus approval.
- Revalidate slot availability inside a transaction.
- Add concurrency-safe capacity enforcement.
- Add idempotency to prevent duplicate requests.
- Implement status transitions and audit events.
- Enforce patient ownership and doctor scope.
- Test simultaneous attempts for the same slot.
Exit criteria:
- Patient can book a slot; overbooking is prevented.
- Retries do not create duplicate appointments.
- Booking reference/status are returned.
- Unauthorized access is rejected.

## Phase 7 — Appointment management
Deliverables: patient and doctor dashboards, cancellation, rescheduling, status history.
Tasks:
- List upcoming and past appointments.
- Implement cancellation cutoff and reasons.
- Implement rescheduling atomically.
- Add approve/reject/complete/no-show actions as configured.
- Ensure released slots become available correctly.
Exit criteria:
- Users see only permitted appointments.
- Cancellation/rescheduling preserve slot integrity and obey policy.
- Status transitions are tested.

## Phase 8 — Ratings, reviews, and trust
Deliverables: source-attributed ratings and (if enabled) first-party review/moderation flow.
Tasks:
- Select permitted rating sources.
- Store source, rating, review count, retrieval date.
- Do not merge platform ratings into one misleading score.
- Define review eligibility and moderation.
Exit criteria:
- Ratings are attributed and dated; unavailable data is not fabricated.
- Moderation is permission-checked and audited.

## Phase 9 — AI Health Assistant
Deliverables: provider-neutral AI service, chat API/UI, safety and error handling.
Tasks:
- Select provider after cost, quality, privacy, and data-term review.
- Define allowed behavior and escalation guidance.
- Provide general health information and broad precautions/diet guidance.
- Avoid diagnosis, prescribing, and personalized treatment decisions.
- Add timeouts, rate limits, usage limits, safe fallback, and mocked tests.
Exit criteria:
- User can ask a general question.
- Limits and uncertainty are clear; provider failure is handled.
- Safety tests pass.

## Phase 10 — Prescription upload and OCR
Deliverables: private upload API/UI, document lifecycle, OCR adapter, extraction review screen.
Tasks:
- Evaluate OCR providers for quality, cost, and privacy.
- Validate type, size, page count, and ownership.
- Store files privately and extract text/confidence.
- Let patient confirm/correct uncertain data.
- Add deletion/retention behavior and upload tests.
- Keep document content out of logs.
Exit criteria:
- Upload works for supported files; extracted text is reviewable.
- Unauthorized access is blocked; deletion policy works.

## Phase 11 — Medicine explanations
Deliverables: trusted drug-reference strategy, per-medicine explanation UI, prescription summary.
Tasks:
- Select a reliable source with permitted use.
- Separate extracted text, reference facts, and AI interpretation.
- Explain common purpose, side effects, precautions, and food instructions only when supported.
- Do not infer a definitive diagnosis or prescriber's intent.
- Never recommend medication changes; ask user to verify unclear medicine/dose.
Exit criteria:
- Explanation is tied to a confirmed medicine identity.
- Source and uncertainty are visible; unsupported medical claims are not presented.

## Phase 12 — Notifications and reminders
Deliverables: booking lifecycle email, delivery records, safe retry strategy, optional reminders.
Tasks:
- Select provider and configure secrets safely.
- Send notifications after transaction commit.
- Prevent duplicate delivery where possible.
- Avoid sensitive details in message previews.
- Add consent/preferences and provider-failure tests.
Exit criteria:
- Notification failures do not corrupt bookings.
- Delivery status and retries are handled.

## Phase 13 — Hardening and end-to-end testing
Deliverables: security/privacy checklist, E2E tests, accessibility review, performance baseline.
Tasks:
- Review auth, object access, uploads, rate limits, CORS, secrets, and logs.
- Test patient booking through confirmation/cancellation.
- Test doctor schedule and appointment management.
- Test AI/OCR uncertainty and provider failures.
- Review keyboard use, labels, focus, contrast, and mobile layout.
- Document database backup/restore and health checks.
Exit criteria:
- Critical flows pass; no known critical access-control issue remains.
- Clean-clone setup is documented and reproducible.

## Phase 14 — Deployment readiness
Deliverables: production configuration, deployment/migration procedure, monitoring and backups.
Tasks:
- Select hosting and database providers.
- Configure TLS, secrets, CORS, rate limiting, storage, and backups.
- Define migration, rollback, recovery, and monitoring.
- Confirm data-source permissions and applicable jurisdiction requirements.
- Complete release checklist before real patient data is accepted.
Exit criteria:
- Deployment is reproducible; backup/restore and rollback are documented.
- Security, privacy, and provider reviews are complete.

## Suggested commit sequence
- docs: add product requirements and architecture
- docs: add phased development roadmap
- chore: scaffold frontend and backend
- chore: add Docker Compose development environment
- feat(auth): add registration and login
- feat(doctors): add doctor profile and credential models
- feat(doctors): add search and profile APIs
- feat(availability): add doctor schedule management
- feat(appointments): add transactional booking
- feat(appointments): add appointment dashboards
- feat(ai): add health assistant foundation
- feat(prescriptions): add private upload and OCR review
- feat(prescriptions): add medicine explanations

Use commit messages that reflect the actual change delivered.

## Progress tracker

| Phase | Status | Notes |
|---|---|---|
| 0. Product definition and repository foundation | Complete | Requirements, architecture, roadmap, and README committed. |
| 1. Project skeleton and local infrastructure | Complete | Frontend opens locally and the Docker Compose stack builds and starts; PostgreSQL port was moved to 5436 in the local `.env` because 5432 and 5433 were occupied. |
| 2. Database and authentication | Complete | Registration/login flow is working locally. Authentication tests and migrations are included; rerun them after pulling if the local database was recreated. |
| 3. Doctor profile data foundation | Complete | Doctor and credential models, optional hospital name on doctor profile, admin management and verification endpoints, fictional demo seed, and migration 0003 are implemented. User confirmed the database migration and test suite passed locally. |
| 4. Doctor search and profile UI | In progress | Added public paginated search and verified-profile detail APIs, responsive directory and profile pages, filters, loading/empty/error states, and public API tests. Local build and tests pending. |
| 5. Doctor availability | Complete | Recurring weekly rules, timezone-aware future-slot generation, admin create/list/delete APIs, migration 0004, and local migration/test verification are complete. Date exceptions, overlap validation, and schedule UI remain future enhancements. |
| 6. Appointment booking core | In progress | Added appointment model/migration, authenticated patient booking API, schedule revalidation, database uniqueness protection, booking references, and patient-owned appointment retrieval. Frontend slot selection/confirmation, idempotency, audit events, and concurrency tests remain. |
| 7. Appointment management | Not started | |
| 8. Ratings, reviews, and trust | Not started | |
| 9. AI Health Assistant | Not started | |
| 10. Prescription upload and OCR | Not started | |
| 11. Medicine explanations | Not started | |
| 12. Notifications and reminders | Not started | |
| 13. Hardening and E2E testing | Not started | |
| 14. Deployment readiness | Not started | |
