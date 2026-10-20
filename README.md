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
- **Collective Voice (AI Spatial Clustering):** Automatically merges nearby duplicate reports ($\le 60\text{m}$) into a single high-priority ticket with elevated citizen weight.
- **Real-Time Officer Sync:** Live background sync alerts field officers instantly with the citizen's photo proof visible directly on dashboard cards.
- **Two-Way Citizen Verification:** No ticket can permanently close without the reporting citizen's confirmation and written feedback. Unsatisfied citizens can reopen tickets with a single click.
- **Multi-Lingual Regional Access:** Instant one-click translation into regional languages (**English, हिन्दी, डोगरी, اردو, ਪੰਜਾਬੀ, کٲشُر**).
- **Automated SLA Hierarchy Escalation:** Time-bound resolution counters trigger automated escalation: Junior Engineer $\rightarrow$ Executive Engineer $\rightarrow$ Municipal Commissioner.

---

## 🌟 Key Innovations & Features

### 1. 📸 Anti-Fraud Ground Intake
- **Viewfinder-Only Camera:** Directly taps into the device camera stream (`navigator.mediaDevices`), preventing stock images or fake photos from being selected.
- **Auto-Locked GPS & Fallback:** Pinpoints high-accuracy coordinates with seamless fallback across all 75 municipal wards of Jammu.
- **Offline-to-Online QR Campaign:** Designed for physical city-wide QR posters at bus stops, markets, and ward offices.

### 2. ⚡ Real-Time Officer Action Console
- **Direct Citizen Photo Proof:** Each complaint card displays the complainant's photo thumbnail with a full-resolution inspection modal.
- **Instant Toast Notification:** When a citizen submits a grievance in one tab, the officer console pops up a real-time toast alert at the bottom-right and prioritizes the ticket to the top.
- **Documented After-Repair Evidence:** Officers upload an after-repair photo proof (camera or gallery) before marking work complete.
- **Public Delay Reasons:** If materials or inter-departmental clearances cause delays, officers openly declare reasons (visible to citizens).

### 3. 🔄 Public Citizen Tracker & Feedback Loop
- **Track & Feedback Navigation Tool:** One-click navbar button with popup search to quickly look up any complaint ID (e.g. `BH-0001`).
- **Before vs After Visual Proof:** Citizens compare the original grievance photo side-by-side with the officer's field repair proof.
- **Citizen Final Say:**
  - **Yes, Issue is Resolved! ✅:** Closes the ticket permanently with citizen comments and feedback.
  - **No, Problem Still Exists 🔄:** Opens an inline description form to explain what is still wrong and reopens the complaint immediately for the officer.
- **SHA-256 Chained Audit Timeline:** Every milestone (created, assigned, clustered, resolved, reopened) is cryptographically logged.

### 4. 🌐 Radical Transparency & City Trust Dashboard
- **City Trust Dashboard:** Real-time civic health score, verified resolution percentages, and ward leaderboard across all 75 wards of Jammu.
- **Public Accountability:** Ward rankings based on response time, closure rate, reopen rate, citizen satisfaction, and proactive broadcasts.

---

## 📱 Application Routes

| Route | Name | Purpose |
|---|---|---|
| `/` | **Public Trust Portal** | 75 Wards civic leaderboard, verified metrics, regional language switcher. |
| `/report` | **Citizen Quick-Report** | Zero-login 30s reporting via live camera stream + GPS auto-lock. |
| `/t/[code]` | **Citizen Tracking & Feedback** | Before/After visual comparison, audit trail, and citizen feedback (Confirm / Reopen). |
| `/officer` | **Officer Action Console** | Priority queue, real-time toast alerts, citizen photo thumbnails. |
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

## 🧪 Demo Data & Quick Testing
To demo the full feedback loop out of the box:
1. Open **`http://localhost:3000`**
2. Click **"Track & Feedback"** in the top navbar.
3. Enter Demo Ticket ID: **`BH-0001`**
4. Review Before & After repair photos and test the **Citizen Feedback** (Confirm Resolution or Reopen with comments).

---

## 📄 License & Attribution
Developed for the **Jammu Smart City Hackathon** by **jaisoni-codes** (`jaisonix11@gmail.com`).  
*CivicHelp Jammu — An open civic trust and accountability initiative for Jammu Municipal Corporation (JMC).*
