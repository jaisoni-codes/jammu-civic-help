# DEMO_CHECKLIST.md — 90-Second Demo & Verification Checklist

## 1. Quick Start Guide
Open two terminals in `C:\Users\NITESH\.gemini\antigravity\scratch\bharosa`:

### Terminal 1: Backend
```powershell
cd C:\Users\NITESH\.gemini\antigravity\scratch\bharosa
$env:PYTHONPATH="."
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Verify: `http://localhost:8000/health` returns `status: ok`.

### Terminal 2: Frontend
```powershell
cd C:\Users\NITESH\.gemini\antigravity\scratch\bharosa\frontend
cmd.exe /c "npm run dev"
```
Open browser at: **`http://localhost:3000`**

---

## 2. 90-Second Demo Script for Judges

| Step | Time | Screen / URL | Action to Click | Evaluator Value |
|---|---|---|---|---|
| **1. The Problem** | 0-15s | `/` | Show **City Trust Score (65/100)** and Ward Leaderboard. | "Complaints are a commodity; trust is not. We measure civic trust with 6 explainable factors." |
| **2. Collective Voice** | 15-35s | `/demo` | Click **"Simulate 3 Nearby Reports"**. | Watch 3 citizens reporting within 40m merge into **1 ticket** (`BH-xxxx`) with **3 Collective Voices**. Priority jumps automatically! |
| **3. Officer Field Proof** | 35-50s | `/officer` | Login as **Rajesh Sharma (PIN: 1234)** → Open the new ticket. | Priority rank, reasons, and SLA countdown chips. Tap **"Accept & Start Work"** → Upload repair proof with live GPS geotagging. |
| **4. Citizen Reopen Escalation** | 50-70s | `/demo` or `/sim` | Tap **"Citizen: NOT SOLVED (No)"**. | Ticket **reopens**, escalation level advances to **L1**, alerts Executive Engineer and supervisor automatically! |
| **5. Closure & Trust Index Moves** | 70-85s | `/demo` | Tap **"Citizen: SOLVED (Yes)"**. | Status becomes **VERIFIED CLOSED**. Open `/ward/1` — the **Ward Trust Index moves live** (e.g. 61 → 65)! |
| **6. Proactive Communication** | 85-90s | `/admin` | Send **Ward 1 Water/Power Broadcast**. | Broadcast lands instantly with citizen delivered confirmation. |

---

## 3. Environment Variables & Safety Fallbacks

| Variable | Default | Purpose |
|---|---|---|
| `MOCK_AI=true` | `true` | Offline deterministic AI: zero quota exhaustion, instant classification, transcription & vision validation. |
| `CHANNEL=console` | `console` | Complete WhatsApp conversation simulation through `/sim` web chat without Meta tokens. |
| `DATABASE_URL` | `sqlite:///./bharosa.db` | Zero-dependency SQLite with spatial Haversine fallback; switch to Postgres anytime. |
| `DEMO_OFFSET_HOURS` | `0.0` | Simulated clock fast-forwardable from `/demo` (+24h, +48h, +72h auto-close). |
