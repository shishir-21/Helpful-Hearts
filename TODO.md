# Helpful Hearts — Master TODO

Snapshot: 2026-10-07
Repository: shishir-21/Helpful-Hearts (FastAPI backend + Next.js web)

Legend: [x] complete, [~] partial/in progress, [ ] todo, [!] blocked/dependent.

## 1. Foundation
- [x] FastAPI + Next.js foundation
- [x] Docker/Docker Compose
- [x] PostgreSQL + SQLAlchemy
- [x] Alembic migrations
- [x] Environment/secret handling
- [x] Health and DB-readiness endpoints
- [x] Backend pytest foundation
- [x] Backend GitHub Actions CI (Ruff + pytest)
- [ ] Keep README and roadmap synchronized with actual code
- [ ] Maintain API documentation for every feature

## 2. Authentication
- [x] Registration
- [x] Login
- [x] Password hashing
- [x] JWT authentication
- [x] Current authenticated user
- [x] Role-based authorization
- [x] Protected routes
- [ ] Email verification
- [ ] Forgot password
- [ ] Reset password
- [ ] Account deletion/deactivation
- [ ] Auth rate limiting/brute-force protection
- [ ] Complete auth security test matrix

## 3. Doctors
- [x] Doctor model
- [x] Credentials/verification foundation
- [x] Optional clinic/hospital name on doctor profile
- [x] Admin doctor management foundation
- [x] Demo doctor seed
- [x] Public doctor search API
- [x] Doctor detail API
- [x] Pagination/search/filter foundation
- [~] Web doctor search/profile experience
- [ ] Search indexes/performance review
- [ ] Sorting
- [ ] Partial-name/spelling-tolerance search
- [ ] Map/geocoding where valid coordinates exist
- [ ] Data provenance and last-verified metadata
- [ ] Approved real doctor-data integrations

## 4. Doctor Availability
- [x] Recurring weekly availability
- [x] Timezone-aware slot generation
- [x] Availability API
- [x] Authorized schedule management
- [x] Availability tests
- [ ] Date exceptions/blocked dates
- [ ] Overlap validation
- [ ] Finalize slot duration/buffers/capacity
- [ ] Finalize booking horizon/lead time
- [ ] Doctor web schedule UI
- [ ] Additional timezone/DST tests

## 5. Appointment Booking
- [x] Appointment model
- [x] Booking API
- [x] Patient authentication/ownership
- [x] Slot and availability revalidation
- [x] Booking reference
- [x] DB uniqueness protection
- [x] Patient appointment retrieval
- [x] Booking UI foundation
- [x] Booking tests
- [ ] Idempotency keys
- [ ] Strong PostgreSQL concurrency tests
- [ ] Complete transaction-level capacity enforcement
- [ ] Complete status transition rules
- [ ] Complete audit/status events
- [ ] Finalize auto-confirm vs approval policy

## 6. Appointment Management
- [x] Patient appointment list
- [x] Cancellation
- [x] Rescheduling
- [x] 12-hour cancellation/rescheduling policy
- [x] Appointment status history
- [x] Patient dashboard controls
- [x] Cancellation/rescheduling tests
- [ ] Doctor appointment dashboard
- [ ] Doctor appointment detail
- [ ] Doctor approve/reject workflow if selected
- [ ] Complete/no-show actions
- [ ] Doctor-only scope tests
- [ ] Verify released-slot integrity in every edge case

## 7. Medical Records
- [ ] Medical-record model
- [ ] Alembic migration
- [ ] Patient-owned record APIs
- [ ] Record detail API
- [ ] Categories/types
- [ ] Ownership/access-control tests
- [ ] Delete/retention policy
- [ ] Audit requirements
- [ ] Web medical-record UI
- [!] Connect Mobile medical-record experience after API contract is verified

## 8. AI Health Assistant
- [ ] Merge/implement authenticated patient assistant backend
- [ ] Conversation ownership
- [ ] Conversation/message persistence
- [ ] Create/list conversations
- [ ] Read messages
- [ ] Send messages
- [ ] Provider-neutral AI service
- [ ] AI provider adapter/configuration
- [ ] Timeout and provider-failure handling
- [ ] Safety/system guidance
- [ ] No diagnosis or autonomous prescribing
- [ ] Rate/usage limits
- [ ] Conversation deletion
- [ ] Safety/provider-failure tests
- [ ] Web assistant UI
- [!] Mobile assistant client already exists; integrate only after backend contract is on main

## 9. Prescriptions + OCR
- [ ] Prescription model
- [ ] Private file-storage contract
- [ ] Upload API
- [ ] Server-side type/size/page validation
- [ ] Ownership/access control
- [ ] OCR adapter/provider
- [ ] OCR extraction + confidence
- [ ] OCR review/update API
- [ ] User correction flow
- [ ] Delete/retention
- [ ] Medicine identity/reference source
- [ ] Medicine explanation service
- [ ] Separate OCR text/reference facts/AI interpretation
- [ ] No medication-change advice
- [ ] Upload/OCR/explanation tests
- [ ] Web prescription UI
- [!] Mobile prescription client already exists; backend contract is required

## 10. Consultation / Telemedicine
- [ ] Consultation session model
- [ ] Appointment authorization
- [ ] Session create/get/end APIs
- [ ] Participant authorization
- [ ] WebRTC signaling
- [ ] Separate consultation chat WebSocket
- [ ] Persist chat messages
- [ ] Consultation history
- [ ] Secure WebSocket authorization
- [ ] TURN for production
- [ ] Consultation tests
- [!] Mobile consultation client already exists; backend contract is required

## 11. Ratings / Reviews / Trust
- [ ] Choose permitted rating sources
- [ ] Store source/rating/count/retrieval date
- [ ] Provenance in API
- [ ] First-party reviews if enabled
- [ ] Review eligibility/reporting/moderation
- [ ] Admin moderation
- [ ] Audit moderation actions

## 12. Notifications
- [ ] Select provider
- [ ] Booking confirmation
- [ ] Cancellation notification
- [ ] Rescheduling notification
- [ ] Appointment reminders
- [ ] Delivery records/retries
- [ ] Send after transaction commit
- [ ] Avoid sensitive preview content
- [ ] Notification preferences/consent
- [!] Coordinate with Mobile push/deep-link implementation

## 13. Admin
- [x] Admin authorization foundation
- [x] Doctor management/verification foundation
- [ ] User administration
- [ ] Verification workflow hardening
- [ ] Security-sensitive audit events
- [ ] Review/report moderation
- [ ] Operational metrics without unnecessary patient data
- [ ] Admin web dashboard

## 14. Redis / Background Jobs
- [ ] Decide first production Redis use cases
- [ ] Rate limiting
- [ ] Safe caching
- [ ] Notification jobs
- [ ] AI/OCR jobs when needed
- [ ] Appointment reminder jobs
- [ ] Worker/queue only when justified
- [ ] Document cache/recovery behavior

## 15. Security / Privacy
- [ ] Full object-level authorization audit
- [ ] IDOR tests for every resource
- [ ] Rate limiting and abuse protection
- [ ] CORS/HTTPS production review
- [ ] Secret-manager configuration
- [ ] Request/correlation IDs
- [ ] Safe structured logging
- [ ] Never log tokens/passwords/health data/prescription contents
- [ ] Upload security/file scanning
- [ ] Retention/deletion implementation
- [ ] Backup/restore procedure
- [ ] Incident-response checklist
- [ ] Launch-jurisdiction/privacy/healthcare review

## 16. Testing / E2E
- [x] Auth/doctor/availability/appointment tests
- [x] CI lint + pytest
- [ ] PostgreSQL integration suite
- [ ] Booking concurrency tests
- [ ] Booking idempotency tests
- [ ] Full authorization matrix
- [ ] Medical-record tests
- [ ] Assistant safety/provider-failure tests
- [ ] Prescription upload/OCR tests
- [ ] Consultation tests
- [ ] Notification tests
- [ ] Patient E2E: register -> login -> doctor -> slot -> booking
- [ ] Patient E2E: booking -> cancellation/reschedule
- [ ] Doctor E2E: schedule -> appointment management
- [ ] Assistant E2E
- [ ] Prescription E2E
- [ ] Consultation E2E

## 17. Production
- [ ] Production Web hosting
- [ ] Production FastAPI hosting
- [ ] Neon PostgreSQL production connection
- [ ] Production migration/rollback procedure
- [ ] Secret management
- [ ] TLS/CORS/rate limits
- [ ] Private object storage
- [ ] Redis/worker deployment if needed
- [ ] Monitoring/error tracking/metrics
- [ ] Database backups + restore drill
- [ ] Release checklist
- [ ] Do not accept real patient data before security/privacy/provider review

## Current execution order
1. [ ] Finish/merge AI Health Assistant backend
2. [ ] Finish Web doctor search/profile
3. [ ] Finish appointment idempotency/concurrency/audit hardening
4. [ ] Finish doctor appointment management
5. [ ] Build medical-record backend
6. [ ] Build prescription/OCR backend
7. [ ] Build consultation backend/signaling/chat
8. [ ] Build notification backend
9. [ ] Integrate and verify Mobile against these contracts
10. [ ] Run complete cross-repo E2E
11. [ ] Security/privacy hardening
12. [ ] Production deployment and release

## Cross-repo rule
Helpful-Hearts is the shared FastAPI backend and Web repository. Helpful-Hearts-Mobile is the Android/iOS client. Never create a separate Mobile backend or invent an API contract in Mobile. Both clients must consume the same versioned backend API.