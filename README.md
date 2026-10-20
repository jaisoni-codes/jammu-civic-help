# CivicHelp Jammu (सिविक हेल्प जम्मू)
> **A Verifiable Civic Trust & Accountability Engine for Jammu Municipal Corporation (JMC)**  
> *Category 05: Welfare for All | Problem Statement: Strengthen Citizen-Municipality Trust through Communication, Responsive Services, Participation, and Feedback Mechanisms.*

---

## 🏛️ Executive Summary

Traditional municipal grievance portals fail on the ground due to a fundamental breakdown of accountability:
1. **Paper/Ghost Closures:** Field tickets are frequently marked "Resolved" without physical inspections.
2. **Duplicate Noise & Clutter:** Neighbors reporting the same broken road create 10 redundant tickets that choke officer queues.
3. **No Verifiable Ground Truth:** Complainants upload random stock photos while officers resolve tickets from distant desks.
4. **Zero Citizen Authority:** The municipality unilaterally decides when an issue is closed, leaving citizens helpless if the problem persists.

**CivicHelp Jammu** turns grievance management into a closed-loop civic accountability operating system:
- **Zero-Login Quick Reporting:** In-browser live camera viewfinder with auto-locked GPS — strictly blocking internet/gallery photo spam.
- **Collective Voice (Spatial Incident Clustering):** Automatically merges nearby duplicate reports ($\le 60\text{m}$) into a single high-priority ticket with elevated citizen weight.
- **Real-Time Officer Sync:** Live background sync alerts field officers instantly with the citizen's photo proof visible directly on dashboard cards.
- **Two-Way Citizen Verification:** No ticket can permanently close without the reporting citizen's confirmation and written feedback. Unsatisfied citizens can reopen tickets with a single click.
- **Multi-Lingual Regional Access:** Instant one-click translation into regional languages (**English, हिन्दी, डोगरी, اردو, ਪੰਜਾਬੀ, کٲشُر**).
- **Automated SLA Hierarchy Escalation:** Time-bound resolution counters trigger automated escalation: Junior Engineer $\rightarrow$ Executive Engineer $\rightarrow$ Municipal Commissioner.

---

## 📸 Visual Tour & Walkthrough

Here is a visual walkthrough of the platform across both citizen and municipal officer workflows:

### 1. 🌐 Public City Trust Portal (`/`)
*Real-time municipal health dashboard showing overall City Trust Score (67.4/100), total active vs verified closures, and competitive ward-by-ward rankings (e.g. Ward 18 Shastri Nagar as Ward Champion).*
![City Trust Portal](./docs/screens/01_city_trust_portal.png)

---

### 2. 🌍 Regional Linguistic Accessibility
*One-click multi-language switcher supporting English, Hindi, Dogri, Urdu, Punjabi, and Kashmiri to eliminate language barriers for citizens across Jammu & Kashmir.*
![Language Selector](./docs/screens/02_language_selector.png)

---

### 3. 🏛️ Full Dogri Real-Time Localization
*The entire platform dynamically translated into Dogri (पब्लिक वार्ड ट्रस्ट सूचकांक, सिविकहेल्प, रिपोर्ट मुद्दा), ensuring zero linguistic exclusion.*
![Dogri Localized Portal](./docs/screens/03_dogri_localized_portal.png)

---

### 4. 📸 Citizen Quick-Report with Live Camera Viewfinder (`/report`)
*Zero-login 30-second intake. Features auto-locked GPS with ward selector fallback, browser-enforced **Live Camera Only** viewfinder (gallery uploads strictly disabled to prevent recycled spam), and instant spatial clustering.*
![Citizen Quick Report](./docs/screens/04_citizen_quick_report.png)

---

### 5. 🤝 Joined Collective Voice & Instant Ticket Tracking
*Automated spatial duplicate clustering joins multiple citizens reporting within 60 meters into a unified high-priority complaint (e.g. `BH-0304` in Janipur Main with 3 citizens backing it), instantly showing their unique tracking code with one-click navigation to the audit chain.*
![Joined Collective Voice](./docs/screens/05_collective_voice_confirmation.png)

---

### 6. ⚡ Officer Action Console with Citizen Photo Proof (`/officer`)
*Live officer inbox featuring citizen-submitted live photo proofs on every card, SLA countdown chips, citizen collective voice counts, and dedicated tabs: **Pending**, **Reopened by Citizen 🔄**, **Awaiting Verify**, and **Completed**.*
![Officer Inbox with Citizen Proof](./docs/screens/06_officer_inbox_with_photos.png)

---

### 7. 🛠️ Officer Resolution Console (`/officer/t/[id]`)
*Officers accept grievances, initiate field crew dispatch, or declare transparent public delay reasons. Work closure requires uploading an after-repair photo proof.*
![Officer Resolution Console](./docs/screens/07_officer_resolution_console.png)

---

### 8. 🔍 Citizen Track & Feedback Navigation Modal
*One-click popup search accessible from any page via the top navigation bar. Citizens simply enter their unique tracking code (e.g. `BH-0001`) to jump directly to their grievance audit trail and feedback console.*
![Track and Feedback Modal](./docs/screens/08_track_and_feedback_modal.png)

---

### 9. 📊 Public Grievance Tracker & Priority Index (`/t/BH-0001`)
*Public audit trail displaying cryptographic SHA-256 verification, Ward Rank #1 of 8 Active Open Issues, and an objective formula-based Transparent Priority Score (24.6/100) preventing VIP favoritism.*
![Tracking Header & Priority](./docs/screens/09_tracking_page_header_priority.png)

---

### 10. 🔄 Verified Photographic Proof & Citizen Feedback Loop
*Before vs After visual comparison. The citizen holds the final authority over closure: they can confirm resolution with feedback comments or reject and reopen the complaint.*
![Citizen Feedback Form](./docs/screens/10_citizen_feedback_resolved_form.png)

---

### 11. ⛓️ Immutable SHA-256 Chained Audit Trail
*Every milestone (Grievance Reported → Assigned to Officer → Escalation → Repair Completed → Citizen Feedback) is cryptographically chained and publicly viewable.*
![Audit Trail Timeline](./docs/screens/11_audit_trail_timeline.png)

---

## 📱 Application Routes

| Route | Name | Purpose |
|---|---|---|
| `/` | **Public Trust Portal** | 75 Wards civic leaderboard, verified metrics, regional language switcher. |
| `/report` | **Citizen Quick-Report** | Zero-login 30s reporting via live camera stream + GPS auto-lock. |
| `/t/[code]` | **Citizen Tracking & Feedback** | Before/After visual comparison, audit trail, and citizen feedback (Confirm / Reopen). |
| `/officer` | **Officer Action Console** | Priority queue, real-time toast alerts, citizen photo thumbnails, Reopened tab. |
| `/officer/t/[id]` | **Resolution Console** | Upload after-repair proof, declare public delays, submit resolution. |
| `/admin` | **Commissioner HQ** | Department workloads, SLA breach escalation monitors, city-wide audit events. |
| `/ward/[id]` | **Ward Deep Dive** | 6-component municipal trust score breakdown and historical trends. |

---

## 🚀 Quick Setup & Run

### 1. Requirements
- Python 3.11+
- Node.js 18+ (tested on v20 & v22)
- Git

### 2. Run Backend (FastAPI)
```powershell
# In repository root
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at `http://localhost:8000/docs`.

### 3. Run Frontend (Next.js)
```powershell
cd frontend
npm install
npm run dev
```
Open **`http://localhost:3000`** in your browser.

---

## 🧪 Step-by-Step Live Demo & Testing Guide

Test the complete closed-loop municipal lifecycle across **Citizen Intake $
ightarrow$ Officer Resolution $
ightarrow$ Citizen Verification**:

### Step 1: 📸 Citizen Quick-Report (`/report`)
1. Open **`http://localhost:3000/report`** (or click **Report Issue** in top navbar).
2. Allow browser camera permission. Your GPS coordinates auto-lock instantly (or select Ward/Locality manually, e.g. *Ward 18 - Shastri Nagar*).
3. The live viewfinder enforces genuine camera capture (file gallery upload is blocked). Click **"Capture Photo"**.
4. Click any quick-tag (e.g. `+ Deep pothole causing traffic jam`) and click **"Submit Grievance Now"**.
5. **Instant Result:** You are assigned a unique tracking code (or automatically joined into **Collective Voice** if a duplicate issue exists within 60 meters).

---

### Step 2: ⚡ Officer Action & Resolution (`/officer`)
1. Open **`http://localhost:3000/officer`** (Officer Console for Rajesh Sharma - Roads & Infrastructure).
2. Observe your reported issue appearing immediately under the **Pending** tab with citizen photo proof, SLA countdown timer, and Priority Score.
3. Click on the grievance card or open **`http://localhost:3000/officer/t/1`** to enter the **Resolution Console**.
4. Test Officer Actions:
   - Click **"Acknowledge & Dispatch Crew"** to set status to in-progress.
   - Click **"Capture After-Repair Proof"** to lock the verified completion photo.
   - Click **"Mark Resolved & Submit to Citizen"** — ticket transitions to *Awaiting Citizen Verification*.

---

### Step 3: 🔄 Citizen Feedback & Closure Verification (`/t/[code]`)
1. Open **`http://localhost:3000`** and click **"Track & Feedback"** in the top navbar.
2. Enter ticket code **`BH-0001`** (pre-seeded resolved demo ticket) or your newly generated code.
3. Compare the verified **Before vs After** repair photos side-by-side.
4. Test the Citizen Feedback Loop:
   - **Option A (Confirm Resolution):** Click *"Yes, Issue is Resolved!"*, add an optional thank-you remark, and submit. Status transitions to **Closed (Citizen Confirmed)**.
   - **Option B (Reopen Grievance):** Click *"No, Problem Still Exists"*, enter a reason (e.g. *"Patch cracked again after morning rain"*), and submit.
5. Switch back to **`http://localhost:3000/officer`**:
   - The grievance immediately moves to the dedicated **"Reopened by Citizen 🔄"** tab with your feedback reason appended directly into the SHA-256 audit trail!

---

## 📄 License & Attribution
Developed for the **Jammu Smart City Hackathon** by **jaisoni-codes** (`jaisonix11@gmail.com`).  
*CivicHelp Jammu — An open civic trust and accountability initiative for Jammu Municipal Corporation (JMC).*
