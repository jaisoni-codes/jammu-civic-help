# Bharosa Jammu (भरोसा जम्मू)
> **A WhatsApp-first Civic Trust Engine for Jammu Smart City**  
> *Category 05: Welfare for All | Problem 3: Strengthen Citizen-Municipality Trust*

---

## 🏛️ Executive Summary
Complaint intake is a commodity. The real challenge in municipal governance is that citizens rarely know if they were heard, priority feels arbitrary, and closures can be fake. 

**Bharosa Jammu** transforms civic reporting into a closed trust loop:
1. **Collective Voice**: Nearby complaints within 60m are coalesced into a single ticket with $N$ voices, elevating collective priority rather than creating duplicate clutter.
2. **Transparent Priority Index**: Formula-based ranking ($0-100$) based on affected citizens, severity, age, safety hazard, and hospital/school proximity.
3. **Verified Field Closure**: Field officers must provide an on-site photo with browser GPS verification ($\le 75\text{m}$) and perceptual hash uniqueness check.
4. **Citizen Authority**: Closures are tentative until the citizen taps **"Solved: Yes/No"**. A "No" reopens and immediately escalates the grievance.
5. **Ward Trust Index**: Live public accountability metric measuring each ward across 6 weighted dimensions.

---

## 🚀 Quick Setup & Run (Zero External Dependencies)

### 1. Requirements
- Python 3.11+
- Node.js 18+ (tested with v22)

### 2. Run Backend
```powershell
cd bharosa
$env:PYTHONPATH="."
python backend/seed/seed.py
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Run Frontend
```powershell
cd bharosa/frontend
npm run dev
```
Open **`http://localhost:3000`** in your browser.

---

## 🧪 Automated Test Suite
To run all unit and integration tests covering P0 through P4:
```powershell
cd bharosa
$env:PYTHONPATH="."
pytest backend/tests/ -v
```
**Results: 13 / 13 Passed.**
- `test_p0_foundation.py`: Health endpoint, database seed idempotency, simulated clock offset.
- `test_p1_intake.py`: Collective voice (3 nearby reports → 1 ticket with affected count = 3), category separation, public ticket API.
- `test_p2_closure.py`: Officer PIN login, verified closure, citizen reopen with escalation +1, perceptual hash duplicate photo rejection, SHA-256 audit chain tamper detection.
- `test_p3_p4_trust_broadcast.py`: Ward Trust Index bounds ($0-100$), proactive broadcasts delivery to target ward, time advancement and SLA escalation.

---

## 📱 Routes & Features
| Route | Description |
|---|---|
| `/` | **City Trust View**: Public Ward Trust Index, live leaderboard, Ward Champion badge, city-wide KPIs. |
| `/ward/[id]` | **Ward Deep Dive**: 6-component breakdown (Response, Closure, Reopen, Satisfaction, Proactive, Participation) + 30-day trajectory. |
| `/t/[code]` | **Public Ticket Tracker**: Explainable priority score & reasons, before/after proof photos, cryptographic SHA-256 audit chain. |
| `/officer` | **Mobile Officer Portal**: Mobile-first priority action inbox with SLA chips (green/amber/red). PIN: `1234`. |
| `/officer/t/[id]` | **Resolution Console**: Accept work, declare public delay reason, capture after-repair photo + GPS geotag. |
| `/admin` | **Commissioner HQ**: Heatmap points, officer workload, proactive broadcast composer. |
| `/sim` | **WhatsApp Simulator**: Web chat simulator for zero-dependency live conversation with intake state machine. |
| `/demo` | **90-Second Demo Panel**: Master control panel for live presentations (simulate 3-person reports, fast-forward time, citizen replies). |

---

## ⏱️ 90-Second Hackathon Demo Script
See [`DEMO_CHECKLIST.md`](./DEMO_CHECKLIST.md) for the complete, step-by-step judge demonstration guide.
