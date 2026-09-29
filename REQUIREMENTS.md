# Helpful Hearts — Product Requirements

Status: Initial product specification | Version: 0.1.0 | Stage: Planning

This document defines planned behavior; it does not mean the features are already implemented.

## 1. Product overview
Helpful Hearts is a web platform for doctor discovery, appointment booking, and AI-assisted health information. The supplied Helpful Hearts screenshot is the visual reference for the doctor discovery experience. The implementation should follow its overall layout and interaction patterns while remaining responsive and accessible.

Core experiences:
- Find Doctors: search and view doctor profiles with sourced, clearly labeled information.
- Appointment Booking: view availability, book, and manage appointments.
- AI Health Assistant: ask general health questions.
- Prescription Analyzer: upload a prescription, review extracted text, and receive a plain-language explanation.

## 2. Goals
- Make doctor discovery easy and useful.
- Display qualifications, experience, clinic affiliations, public contact details, and ratings with provenance and verification status.
- Support reliable booking with transactional protection against double booking.
- Let patients and doctors manage appointments according to defined permissions.
- Explain health and prescription information without replacing a licensed clinician.
- Build incrementally using Python, FastAPI, PostgreSQL, and Docker.
- Keep documentation, tests, and implementation aligned.

## 3. Initial non-goals
- Diagnosing diseases or inferring a definitive diagnosis from symptoms or a prescription.
- Autonomous prescribing or advice to start, stop, or change medication or dosage.
- Emergency care or clinical triage as a substitute for emergency services.
- Guaranteed integrations with every hospital, rating platform, or booking provider.
- Payments, insurance, EHR integration, telemedicine, and native mobile apps unless approved in a later phase.
- Treating ratings or AI-generated summaries as proof of clinical quality.

## 4. User roles
### Visitor
Browse and search public profiles; view booking instructions; register/sign in to perform patient actions.

### Patient
Manage account; search doctors; view profiles and availability; book, view, cancel, or reschedule appointments; use the AI assistant; upload and review prescriptions; delete uploaded files subject to retention policy.

### Doctor
Maintain a profile; submit qualifications and registration details for verification; manage clinic affiliations and public booking details; configure schedules and blocked dates; view and manage appointments only within their authorized scope.

### Administrator
Manage users, doctors, hospitals, affiliations, verification, reports, and moderation. Administrative actions must be permission-checked and audited.

## 5. Functional requirements
Priority: P0 = initial usable release; P1 = next iteration; P2 = later.

### 5.1 Authentication and accounts
- AUTH-001 (P0): Patient registration, login, and logout.
- AUTH-002 (P0): Secure password hashing; never store plaintext passwords.
- AUTH-003 (P0): Protect authenticated API routes.
- AUTH-004 (P0): Enforce authorization on the server, including object-level access.
- AUTH-005 (P0): Support patient, doctor, and administrator roles.
- AUTH-006 (P1): Email verification and password reset.
- AUTH-007 (P1): Account deactivation/deletion and associated data policy.

### 5.2 Doctor search
- DOC-001 (P0): Search doctors by name.
- DOC-002 (P0): Filter by specialty and location when data is available.
- DOC-003 (P0): Paginate results and provide loading, empty, and error states.
- DOC-004 (P0): Result cards show name, specialty, experience, clinic/hospital, location, and booking action when known.
- DOC-005 (P1): Sorting by supported fields such as name, experience, distance, or rating, with clear definitions.
- DOC-006 (P1): Map display for geocoded clinics, with an accessible list alternative.
- DOC-007 (P1): Partial-name matching and practical spelling tolerance.
- DOC-008 (P0): Never fabricate doctor records. Demo data must be labeled as demo data.

### 5.3 Doctor profiles and trust
- PROFILE-001 (P0): Show name, specialty, qualifications/degrees, experience, languages, and biography when supplied.
- PROFILE-002 (P0): Show current and historical clinic/hospital affiliations with status and dates where available.
- PROFILE-003 (P0): Show registration information and verification status only when supported by evidence.
- PROFILE-004 (P0): Show public phone, assistant/reception contact, email, address, and booking instructions only when authorized for publication.
- PROFILE-005 (P0): Show data source and last-updated/verified date for material information.
- PROFILE-006 (P0): Distinguish verified, doctor-submitted, imported, demo, and unknown information.
- PROFILE-007 (P1): Support profile/clinic images with consent and licensing checks.
- PROFILE-008 (P1): Show ratings only when source access and reuse are permitted; include source, review count, and retrieval date.
- PROFILE-009 (P0): Do not generate an AI reliability score. Show evidence fields separately; ratings are not proof of clinical outcomes.

### 5.4 Hospitals and clinics
- HOSP-001 (P0): Store name, address, city, contact details, and optional coordinates.
- HOSP-002 (P0): A doctor may have multiple affiliations.
- HOSP-003 (P0): Track affiliation status and validity dates to avoid presenting outdated workplaces as current.
- HOSP-004 (P1): Clinic detail pages and associated doctor lists.
- HOSP-005 (P1): Verified clinic schedules and directions where available.

### 5.5 Availability and booking
- BOOK-001 (P0): Patients can view available dates and slots for a doctor.
- BOOK-002 (P0): Doctors/authorized staff can configure recurring weekly availability and exceptions.
- BOOK-003 (P0): Availability includes timezone, working hours, slot duration, buffers, and capacity as configured.
- BOOK-004 (P0): Patients can select a slot and submit required contact/visit details.
- BOOK-005 (P0): Backend revalidates availability during booking.
- BOOK-006 (P0): Concurrent requests cannot exceed configured slot capacity; use transactions and database constraints/locking.
- BOOK-007 (P0): Successful booking receives a unique, non-guessable booking reference.
- BOOK-008 (P0): Explicit statuses: pending, confirmed, rejected, cancelled, completed, and no-show as applicable.
- BOOK-009 (P0): Support automatic confirmation or doctor/staff approval.
- BOOK-010 (P0): Patients can view upcoming and past appointments.
- BOOK-011 (P0): Patients can cancel according to configured policy.
- BOOK-012 (P1): Patients can request/perform rescheduling according to policy and availability.
- BOOK-013 (P0): Doctors/staff can access only appointments in their authorized scope.
- BOOK-014 (P0): Store instants consistently in UTC and display in clinic timezone.
- BOOK-015 (P0): Record timestamps and relevant status changes.
- BOOK-016 (P1): Send confirmation, cancellation, rescheduling, and reminder notifications.
- BOOK-017 (P1): Configure booking horizon, lead time, cancellation cutoff, and appointment duration.
- BOOK-018 (P1): Support in-person/online types only where actually offered.
- BOOK-019 (P2): Add payments only after provider, refund, and compliance decisions.

### 5.6 Ratings and reviews
- REV-001 (P1): Display source, rating, review count, and last-fetched date.
- REV-002 (P1): Do not combine ratings from different platforms into a misleading score.
- REV-003 (P1): Do not imply ratings establish medical competence or outcomes.
- REV-004 (P1): First-party reviews require eligible appointment or documented moderation rules.
- REV-005 (P1): Support reporting and moderation.

### 5.7 AI health assistant
- AI-001 (P0): Authenticated users can ask general health-information questions.
- AI-002 (P0): Clearly frame answers as general information, not diagnosis or personalized treatment.
- AI-003 (P0): Do not prescribe or advise starting, stopping, or changing medication/dosage.
- AI-004 (P0): Communicate uncertainty and ask clarifying questions when needed.
- AI-005 (P0): Encourage professional care for concerning symptoms and emergency care for potentially urgent symptoms.
- AI-006 (P0): Avoid unsupported claims; use reliable medical references where feasible and expose references when available.
- AI-007 (P0): Do not present chat as a substitute for clinician evaluation.
- AI-008 (P1): Conversation history and deletion controls.
- AI-009 (P1): Rate limits, usage limits, timeouts, and provider-failure handling.

### 5.8 Prescription upload and explanation
- RX-001 (P0): Upload supported image/PDF prescriptions within configured size/type limits.
- RX-002 (P0): Validate files server-side and store privately.
- RX-003 (P0): Extract text using OCR and retain confidence/uncertainty where available.
- RX-004 (P0): Let users confirm/correct uncertain medicine names and instructions.
- RX-005 (P0): Explain identified medicines' common purpose, side effects, precautions, and food instructions using reliable drug information.
- RX-006 (P0): Distinguish prescription text, reference facts, and AI interpretation.
- RX-007 (P0): Do not infer a definitive diagnosis or prescriber's actual intent from a prescription alone.
- RX-008 (P0): Do not advise medication changes; refer regimen questions to a clinician/pharmacist.
- RX-009 (P0): Never guess an unclear medicine or dose; ask the user to verify it.
- RX-010 (P0): Provide deletion and retention controls.
- RX-011 (P1): Support multi-page documents and page order.
- RX-012 (P1): Allow export/share only through explicit user action and privacy safeguards.

### 5.9 Notifications
- NOTIF-001 (P1): Notify about booking confirmation, cancellation, and rescheduling.
- NOTIF-002 (P1): Reminders must avoid sensitive medical details in previews.
- NOTIF-003 (P1): Track delivery and retry safely without duplicating bookings.
- NOTIF-004 (P2): SMS/WhatsApp/push only after provider, consent, and policy review.

### 5.10 Administration
- ADMIN-001 (P0): Admin endpoints require administrator authorization.
- ADMIN-002 (P0): Admins can review doctor verification submissions.
- ADMIN-003 (P0): Audit security-sensitive administrative actions.
- ADMIN-004 (P1): Moderate reported profiles and reviews.
- ADMIN-005 (P1): Provide operational metrics without unnecessary patient data.

## 6. Non-functional requirements
### Performance
- Paginate and index search.
- Avoid unnecessary queries and oversized responses.
- Apply timeouts to AI/OCR and use background processing when long-running work is introduced.
- Keep local development resource-conscious.

### Reliability
- Booking writes are transactional and retries are idempotent where applicable.
- External provider failures are handled gracefully.
- Notification failure must not undo a committed booking.
- Database migrations are versioned and reproducible.

### Security and privacy
- Use HTTPS in production.
- Keep secrets outside source control.
- Enforce role and object-level access.
- Validate input; protect against injection, broken access control, brute force, and abuse.
- Validate upload size/type and store files privately.
- Minimize personal and health data collection.
- Define consent, retention, deletion, backup, and incident response before production.
- Never log passwords, tokens, prescription contents, or unnecessary health data.
- Review applicable privacy and healthcare requirements for the launch jurisdiction.

### Accessibility and maintainability
- Responsive desktop/tablet/mobile UI.
- Keyboard navigation, labels, focus states, contrast, and meaningful errors.
- Plain-language patient-facing explanations.
- Separate routes, schemas, business logic, persistence, and integrations.
- Use type hints, formatting, linting, and tests.

## 7. Data/source requirements
- Doctor records require provenance and last-verified metadata.
- Use third-party data only when its terms permit access and reuse.
- Ratings/contact details must not be fabricated or presented as verified without evidence.
- Keep demo data visibly separate from real profiles.
- Provide a correction workflow for stale or inaccurate records.

## 8. Initial release acceptance criteria
- Patient can register and sign in.
- Search seeded demo doctors and open profiles.
- Authorized doctor/admin can configure availability.
- Patient can book a slot; concurrent requests cannot overbook it.
- Patient can view and cancel an appointment according to policy.
- Doctor can access only appointments in their scope.
- AI assistant returns safety-framed general information and handles provider errors.
- Patient can upload a sample prescription, review extracted text, and receive a clearly labeled explanation without diagnosis or medication-change advice.
- App starts using documented Docker Compose commands.
- Automated tests cover authorization and booking rules.

## 9. Open decisions
- Launch jurisdiction and applicable requirements.
- Doctor onboarding and verification evidence.
- Doctor directory, ratings, and drug-information sources and permissions.
- Auto-confirmation versus approval policy.
- Slot duration, capacity, booking horizon, cancellation, and rescheduling rules.
- Online consultation and payment scope.
- AI/OCR provider, budget, data terms, and retention.
- Hosting, backups, monitoring, and support.

## 10. Delivery principles
Build incrementally, keep the main branch runnable, make small descriptive commits, add tests and documentation with each feature, and do not mark a feature complete until its acceptance criteria pass.
