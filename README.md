# ClassPulse

> **AI-Powered School Intelligence & Proactive Student Support System**

ClassPulse is a modern, enterprise-grade multi-tenant educational intelligence platform designed to detect student learning, attendance, and behavioral challenges early—giving teachers and school leaders actionable, explainable insights before small issues compound into academic failure or dropouts.

---

## 🌟 Smart Automatic Intervention Recommendation System

The **Smart Automatic Intervention Recommendation System** bridges the gap between AI risk detection and concrete educator action. When ClassPulse calculates a student's risk score, the recommendation engine evaluates multi-signal trends, historical reports, and prior interventions to answer:

> **"What should the educator do next to support this student?"**

### 🛡️ Core Design Philosophy: Human-in-the-Loop & Advisory Only
- **Zero Automated Actions**: ClassPulse **never** sends automated SMS, makes automated phone calls, or imposes punitive measures.
- **Strictly Advisory**: Every recommendation is an educator-facing recommendation awaiting manual review and confirmation.
- **Explainable & Action-Oriented**: Each recommendation provides plain-language explanations, specific trigger signals (e.g. *Attendance dropped 18% below baseline*), and recommended concrete steps.
- **Teacher Discretion**: Educators can customize the intervention type, add individualized notes, select follow-up dates, or dismiss non-actionable suggestions with a documented rationale.

---

## ⚙️ Deterministic Recommendation Engine (Rules 1–9)

The recommendation engine employs deterministic, auditable pedagogical decision trees rather than black-box approximations:

| Rule | Trigger Condition | Recommended Intervention | Priority Level | Rationale & Suggested Actions |
|---|---|---|---|---|
| **1. Severe Attendance Drop** | Attendance Drop $\ge 15\%$ | `PARENT_CONTACT` / `ATTENDANCE_SUPPORT` | **HIGH** or **URGENT** | Sudden or steep drop in school presence. Inquire into home or transport challenges. |
| **2. Homework Disengagement** | Homework Drop $\ge 20\%$ | `ACADEMIC_SUPPORT` / `ONE_ON_ONE_CHECKIN` | **MEDIUM** or **HIGH** | Assignments missing or late. Review workload balance and task clarity. |
| **3. Subject-Specific Decline** | Academic Test Drop $\ge 15\%$ | `ACADEMIC_SUPPORT` (with subject targeted) | **MEDIUM** or **HIGH** | Identifies specific subject (e.g., Mathematics) and recommends peer tutoring or remedial review. |
| **4. Multi-Signal Compound Decline** | Declines across 2+ signals | Multi-tiered (`PARENT_CONTACT` + `ACADEMIC_SUPPORT`) | **HIGH** or **URGENT** | Compounding risk indicating acute stress across attendance and grades. |
| **5. Persistent Multi-Week Decline** | $\ge 2$ consecutive weeks of decline | Escalated `COUNSELING_REFERRAL` | **URGENT** | Chronic unaddressed decline requiring dedicated student counselor intervention. |
| **6. Sudden Academic / Behavioral Drop** | Acute drop $\ge 25\%$ in period | Immediate `ONE_ON_ONE_CHECKIN` / `PARENT_CONTACT` | **URGENT** ($\ge 75$ Priority) | Rapid change in behavior; requires immediate teacher check-in within 48 hours. |
| **7. Temporary Recovery** | Previous Risk $\ge 60$ and Current Risk $\le 35$ | `FOLLOW_UP_REVIEW` | **LOW** (Priority 30) | Acknowledges rebound; suggests light praise and scheduled review rather than aggressive intervention. |
| **8. Naturally Low but Stable** | Risk $\le 35$ with Stable Baseline | No Action or Low-Priority `PEER_SUPPORT` | **LOW** | Prevents false alarms on steady learners with naturally lower marks. |
| **9. Insufficient Data** | New admission or $< 3$ records | Information Gathering Action | **LOW** | Recommends establishing baseline observation rather than remedial intervention. |

---

## ⏱️ Cooldown & Duplicate Prevention Engine

To prevent recommendation fatigue and conflicting outreach to families, the engine queries all previous interventions in Firestore:

- **Configurable Cooldown Windows**:
  - `ONE_ON_ONE_CHECKIN`: 7 days
  - `PARENT_CONTACT`: 14 days
  - `ACADEMIC_SUPPORT`: 14 days
  - `COUNSELING_REFERRAL`: 21 days
  - `ATTENDANCE_SUPPORT`: 14 days
  - `PEER_SUPPORT`: 14 days
  - `FOLLOW_UP_REVIEW`: 14 days
- **Active / Planned Suppression**: Suppresses duplicate proposals if an intervention of that type is already `IN_PROGRESS` or `PLANNED`.
- **Urgent Override**: If a student experiences an acute **sudden drop ($\ge 25\%$)** or **persistent multi-signal decline**, the cooldown is overridden with explicit reasoning flagged on the recommendation card.
- **Outcome Awareness**: If a previous intervention was `COMPLETED` with outcome `STUDENT_UNCHANGED` or `STUDENT_WORSENED`, the engine escalates to higher-tier interventions (e.g., from check-in to counseling).

---

## 🔒 Security, RBAC & Multi-Tenant Isolation

- **Tenant Isolation**: Every Firestore query strictly filters by `school_id`. Attempting to access recommendations across schools returns `HTTP 403 Forbidden`.
- **Role-Based Access Control (RBAC)**:
  - **`TEACHER`**: Authorized to view, filter, approve, and dismiss recommendations for their assigned classes and students.
  - **`SCHOOL_ADMIN` / `ADMIN` (Principal)**: Full school-wide visibility across all classes, summary KPIs, and executive oversight.
  - **`STUDENT`**: **Strictly blocked with `HTTP 403 Forbidden`**. Recommendations and risk calculations are educator-confidential.

---

## 🔌 API Endpoints

All endpoints follow the standard ClassPulse response envelope `{"success": true, "data": ..., "error": null}`:

```http
# Run on-demand recommendation analysis for a student
POST /api/v1/intervention-recommendations/student/{student_id}/analyze

# Fetch recommendations for a student (with status/priority filters)
GET  /api/v1/intervention-recommendations/student/{student_id}?status=PENDING

# Fetch recommendations for an entire class
GET  /api/v1/intervention-recommendations/class/{class_id}?status=PENDING

# Fetch school-wide recommendations (School Admin / Principal only)
GET  /api/v1/intervention-recommendations/school/{school_id}

# Approve recommendation (converts to active Intervention record)
POST /api/v1/intervention-recommendations/{id}/approve
Payload: { "intervention_type": "...", "notes": "...", "follow_up_date": "YYYY-MM-DD" }

# Dismiss recommendation with documented reason
POST /api/v1/intervention-recommendations/{id}/dismiss
Payload: { "reason": "Student was absent due to verified medical leave." }
```

---

## 💻 User Interface & Features

### 1. Teacher Recommendations Feed (`/teacher/recommendations`)
- **Interactive KPI Header**: Instant counts of Pending Review, Urgent Priority, High Priority, and Approved Interventions.
- **Multi-dimensional Filters**: Filter by Class, Priority Level (Urgent, High, Medium, Low), and Status (Pending, Approved, Dismissed).
- **Rich Recommendation Cards**:
  - Priority badge with color coding (Red for Urgent, Orange for High, Yellow for Medium, Green for Low).
  - Risk score pill and declining signal badges (e.g. *Attendance ↓ 20%*, *Academics ↓ 16%*).
  - Full natural-language explanation and recommended concrete action steps.
  - Previous intervention context (e.g. *Prior check-in completed on Aug 20*).
- **Approve Modal**: Pre-populates recommended type and notes with custom date picker and one-click conversion to an active intervention.
- **Dismiss Modal**: Clean dismissal modal with mandatory reason capture for auditability.

### 2. Principal Support Oversight (`/principal/intervention-recommendations`)
- **School-Wide Analytics**: Overview metrics showing conversion rate and urgent cases across all grades.
- **Dual View Modes**: Switch between **Table View** (dense, sortable) and **Card View** (comprehensive).
- **Principal Dashboard Integration**: "School Support Recommendations" widget on the main dashboard providing direct navigation.

### 3. Student Detail Embedded Recommendations (`StudentDetailPage.tsx`)
- Contextual "Smart Intervention Recommendations" card directly alongside student marks, attendance trends, and past interventions.
- Direct "Accept Recommendation" button allowing teachers to act while reviewing student records.

---

## 🧪 Testing & Verification

ClassPulse maintains a 100% passing test suite across both frontend and backend:

### Backend Tests (172 Tests)
Run pytest from `server/`:
```bash
cd server
.venv\Scripts\pytest tests/ -v
```
- Covers unit tests for all 9 deterministic recommendation rules, priority score calculations, cooldown windows, and outcome escalations.
- Covers integration tests for RBAC enforcement (Teacher allowed, Principal allowed, Student blocked with 403, Cross-school blocked with 403).
- **Result: 172 passed, 0 failed in 16.4s.**

### Frontend Build
Run Vite build from `client/`:
```bash
cd client
npm run build
```
- Full TypeScript compilation (`tsc -b`) and asset bundling with zero errors.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (tested with Python 3.14)
- Node.js 18+ and npm
- Firebase Project or local mock Firestore

### Backend Setup
```bash
cd server
python -m venv .venv
.venv\Scripts\activate   # Windows (.venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd client
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.
