# PLAN.md - Bharosa Jammu Implementation Plan

## Overview
**Bharosa Jammu** is a WhatsApp-first civic trust engine for the Jammu Smart City Hackathon (Category 05: Welfare for All | Problem 3: Strengthen citizen-Municipality trust).
Citizens report civic issues, officers close them with geotagged proof + photo verification, citizens verify the closure, and a public Ward Trust Index (0-100) measures and displays trust transparently per ward.

---

## Phases & Acceptance Criteria

### Phase P0: Foundation & Core Setup
- **Tasks**:
  1. Initialize project structure (`bharosa/backend/app/{models,services,channels,api}`, `frontend/`, config, clock).
  2. Configure environment (`.env.example`, `.env`) with fallback defaults (`MOCK_AI=true`, `CHANNEL=console`).
  3. Setup database layer: PostgreSQL + PostGIS support via SQLAlchemy 2 + Alembic, with SQLite/SpatiaLite fallback for zero-dependency standalone execution when docker/PostGIS is absent locally.
  4. Implement `clock.py` with `DEMO_OFFSET_HOURS` support for fast-forwarding time in demo scenarios.
  5. Build `seed.py`: 10 Jammu demo wards, 8 departments, 12 officers, 25 POIs, 300 synthetic historical tickets, 400 synthetic citizens, Mohalla projects.
  6. Health check endpoint `/health`.
- **Acceptance Check**:
  - `make dev` or `python -m backend.app.main` starts cleanly.
  - `make seed` runs idempotently.
  - `GET /health` returns `{"status": "ok", "time": ...}`.

### Phase P1: Intake & Collective Voice
- **Tasks**:
  1. `ChannelAdapter` abstraction interface (`base.py`) with `ConsoleAdapter`, `TelegramAdapter`, `WhatsAppCloudAdapter`.
  2. AI Service (`ai.py`): Gemini client via `google-genai` with deterministic mock mode (`MOCK_AI=true`).
  3. Intake flow state machine (Language -> Report -> Location pin / Ward fallback -> Confirmation).
  4. Collective Voice (Duplicate clustering): merge reports within 60m + 14d + same category + embedding similarity >= 0.80 into single ticket with `affected_count += 1`.
  5. Transparent Priority scoring service (`priority.py`) with human-readable reason explanations.
  6. Public ticket API (`GET /api/public/tickets/{code}`).
- **Acceptance Check**:
  - Tests prove 3 nearby pothole reports coalesce into 1 ticket with `affected_count = 3`.
  - Reports in different categories or >60m apart create separate tickets.

### Phase P2: Officer & Verified Closure
- **Tasks**:
  1. Simple JWT auth for officers/admins (seeded officer PIN login).
  2. Officer API: list inbox sorted by priority score, view ticket, accept, block with reason code, resolve with photo + GPS.
  3. Verification safeguards:
     - Distance check: officer GPS vs ticket coordinates (reject > 75m unless mismatch reason given).
     - Perceptual hash reuse check (Pillow + `imagehash` hamming distance < 6 against before-photo or previous closures).
     - Gemini vision check: flag `needs_review` if confidence < 0.5 or not resolved (AI flags, never closes).
  4. Citizen verification loop (`Solved? Yes/No` + rating 1-5).
  5. Reopen trigger: "No" escalates level (+1) and notifies officer/supervisor.
  6. SLA escalation & 72h auto-close scheduler jobs.
  7. Tamper-evident SHA-256 hash-chained audit log with integrity verification endpoint (`/verify-chain`).
- **Acceptance Check**:
  - Tests: Reopen raises escalation level; reused photo is rejected; audit chain tamper is detected.

### Phase P3: Trust Engine & Public UI
- **Tasks**:
  1. Ward Trust Index computation service: 6 weighted components (Response, Verified closure, Reopen, Satisfaction, Proactive, Participation).
  2. Trust snapshots table & daily/periodic recomputation.
  3. Public Frontend Pages (Next.js 14 App Router + Tailwind + Leaflet + Recharts):
     - `/`: City Trust Index, interactive map, Ward Leaderboard with improvement trends and Champion badge.
     - `/ward/[id]`: Ward drilldown with 6-component breakdown, 30-day trend chart, open vs closed vs reopened, Mohalla voting.
     - `/t/[code]`: Public ticket view with audit timeline, "You and N others", transparent priority explanation, before/after proof photos, hash-chain valid badge.
- **Acceptance Check**:
  - Unit tests verify each Trust Index component formula and redistribution when data is sparse.
  - UI shows updated trust score immediately after ticket resolution and verification.

### Phase P4: Communication & Participation
- **Tasks**:
  1. Ward-wise proactive broadcasts API & channel delivery (water, power, road alerts).
  2. "You Said, We Did" monthly digest service & trigger.
  3. Monthly Pulse survey question & response tracking.
  4. Mohalla Budget voting: 3-5 projects per ward cycle, 1 vote per citizen per cycle.
- **Acceptance Check**:
  - Broadcast reaches only citizens subscribed to that ward.
  - Citizen cannot vote twice in the same cycle.

### Phase P5: Polish & 90-Second Demo
- **Tasks**:
  1. `/sim`: Web chat simulator running ConsoleAdapter for instant WhatsApp-like demo without external credentials.
  2. `/demo`: Master demo control panel (simulate 3-person complaint, advance time by hours, simulate citizen Yes/No reply, trigger SLA jobs, reset state).
  3. Officer Mobile UI (`/officer`, `/officer/t/[id]`): Mobile-first inbox, SLA chips, camera capture, GPS geotagging.
  4. Admin Commissioner view (`/admin`): Heatmap, officer workload, escalation tracker, broadcast composer.
  5. Complete documentation: `README.md`, `DEMO_CHECKLIST.md`, Makefile, 90-second demo script.
- **Acceptance Check**:
  - Full 90-second demo executes end-to-end reliably: 3 complaints -> 1 ticket -> Officer resolves with photo -> Citizen taps "No" -> Reopen & escalate -> Re-resolve -> Citizen taps "Yes" -> Ward Trust Index increases -> Ward broadcast sent.
