# ClassPulse API

> **AI-driven early learning-gap detection system**  
> Phase 2 — Data & Student Management

ClassPulse detects students showing signs of academic decline **weeks before
conventional exams reveal the problem**, giving teachers explainable,
actionable early warnings based on data schools already generate.

---

## Table of Contents

- [Project Status](#project-status)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Firebase Setup](#firebase-setup)
- [Running the Server](#running-the-server)
- [API Documentation](#api-documentation)
- [Running Tests](#running-tests)
- [Production Deployment](#production-deployment)
- [Development Phases](#development-phases)
- [Security Notes](#security-notes)

---

## Project Status

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | Server / Foundation Setup | ✅ Complete |
| **Phase 2** | Data Ingestion & Student Management | ✅ Complete |
| Phase 3 | AI/ML Risk Detection | 🔜 Next |
| Phase 4 | Teacher Dashboard & Intervention System | 🔜 Not started |
| Testing | Comprehensive Test Suite | 🔜 Not started |


---

## Architecture Overview

```
React (Vite)
    │
    │  Firebase ID Token (Bearer)
    ▼
FastAPI (Python)          ← Business logic, auth, ML orchestration
    │
    ├── Firebase Auth     ← Token verification (Admin SDK)
    ├── Cloud Firestore   ← Application data
    └── Firebase Storage  ← Raw uploaded files (Phase 2+)
```

**Separation of concerns:**

| Layer | Responsibility |
|---|---|
| React | UI only |
| Firebase Auth | Identity / token issuance only |
| FastAPI | All business logic, authorisation, ML orchestration |
| Firestore | Persistent application data |
| Firebase Storage | Raw file uploads (CSV, Excel) |

---

## Project Structure

```
server/
├── app/
│   ├── main.py                     # App factory, middleware, exception handlers
│   ├── core/
│   │   ├── config.py               # Pydantic Settings (all env vars)
│   │   ├── firebase.py             # Firebase Admin SDK initialisation
│   │   ├── logging.py              # Structured logging (JSON in prod)
│   │   └── security.py             # Auth dependency, CurrentUser, roles
│   ├── middleware/
│   │   └── request_logging.py      # Request ID, timing, access logs
│   ├── api/
│   │   ├── deps.py                 # Shared FastAPI dependencies
│   │   ├── router.py               # Top-level router (mounts v1)
│   │   └── v1/
│   │       └── health.py           # GET /api/v1/health, /health/firebase
│   ├── utils/
│   │   └── responses.py            # Standard response helpers
│   ├── models/                     # (Phase 2+) Domain models
│   ├── schemas/                    # (Phase 2+) API schemas
│   └── services/                   # (Phase 2+) Business logic services
├── tests/
│   ├── conftest.py                 # Fixtures, Firebase mocking
│   └── v1/
│       └── test_health.py          # Health endpoint tests
├── .env.example                    # Environment template
├── .gitignore
├── requirements.txt
├── run.py                          # Local dev entry point
└── README.md
```

---

## Prerequisites

- **Python 3.11+** (3.12 recommended)
- **pip** or **pipx**
- A **Firebase project** (for full Firebase connectivity)

---

## Quick Start

### 1. Clone the repository

```bash
git clone <repo-url>
cd server
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in your Firebase credentials (see [Firebase Setup](#firebase-setup)).

### 5. Start the development server

```bash
python run.py
```

The server will start at **http://localhost:8000**

---

## Environment Variables

All configuration is done via environment variables. Never commit `.env` or any credentials file.

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_ENV` | No | `development` | `development` \| `staging` \| `production` |
| `APP_NAME` | No | `ClassPulse API` | API title (shown in /docs) |
| `APP_VERSION` | No | `1.0.0` | API version |
| `HOST` | No | `0.0.0.0` | Server bind address |
| `PORT` | No | `8000` | Server port |
| `FIREBASE_PROJECT_ID` | **Yes** | — | Firebase project ID |
| `FIREBASE_CLIENT_EMAIL` | **Yes** | — | Service account email |
| `FIREBASE_PRIVATE_KEY` | **Yes** | — | Service account private key |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Comma-separated allowed origins |
| `LOG_LEVEL` | No | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| `HIDE_ERROR_DETAILS` | No | `false` | Set `true` in production |

---

## Firebase Setup

### Step 1: Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use an existing one
3. Enable **Cloud Firestore** and **Firebase Authentication**

### Step 2: Generate a Service Account Key

1. Firebase Console → **Project Settings** → **Service Accounts**
2. Click **Generate new private key**
3. Download the JSON file

> ⚠️ **NEVER commit this file to version control.**  
> It is already in `.gitignore` but treat it as a secret.

### Step 3: Extract credentials to `.env`

From the downloaded JSON, copy these values to your `.env`:

```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
```

**Important:** Wrap the private key in double quotes in `.env`. The `\n` characters
must remain as literal `\n` — not actual newlines — in the file.

### Step 4: Enable Email/Password Authentication

Firebase Console → **Authentication** → **Sign-in methods** → Enable **Email/Password**

---

## Running the Server

### Development (with hot-reload)

```bash
python run.py
```

### Manual uvicorn

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## API Documentation

With the server running, open:

| URL | Description |
|---|---|
| http://localhost:8000/docs | Swagger UI (interactive) |
| http://localhost:8000/redoc | ReDoc (readable) |
| http://localhost:8000/openapi.json | OpenAPI schema |

### Available Endpoints (Phase 1)

```
GET /                       → Service info and links
GET /api/v1/health          → Liveness probe
GET /api/v1/health/firebase → Firebase connectivity probe
```

### Response Format

All responses use a consistent envelope:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00.000000+00:00"
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "AUTH_TOKEN_INVALID",
    "message": "The provided token is invalid.",
    "details": null
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00.000000+00:00"
  }
}
```

---

## Running Tests

Tests use mocked Firebase — **no real Firebase credentials are needed** to run tests.

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest tests/ -v --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/v1/test_health.py -v
```

---

## Production Deployment

### Google Cloud Run (Recommended)

**Do NOT use a `.env` file or service account JSON in production.**

Instead:

1. **Service Account**: Create a dedicated service account with minimal permissions
   (Firestore User, Storage Object Admin).

2. **Assign to Cloud Run**: In Cloud Run settings, set the service account.
   The Firebase Admin SDK will automatically use the Cloud Run identity
   (`google.auth.default()`).

3. **Application settings**: Set non-sensitive env vars directly in Cloud Run:
   ```
   APP_ENV=production
   HIDE_ERROR_DETAILS=true
   CORS_ORIGINS=https://your-frontend-domain.com
   ```

4. **Secrets** (if not using Cloud Run identity): Store `FIREBASE_PRIVATE_KEY`
   in **Secret Manager** and mount as an environment variable.

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## Development Phases

### Phase 1 — Server Foundation ✅
FastAPI server, Firebase integration, auth dependency, CORS, logging, health endpoints.

### Phase 2 — Data Ingestion & Student Management 🔜
Schools, teachers, classes, students, CSV upload pipeline, validation, normalisation.

### Phase 3 — AI/ML Risk Detection 🔜
Weekly engagement signatures, student baselines, trend detection, risk scoring, explainability.

### Phase 4 — Teacher Dashboard & Intervention System 🔜
React frontend, student risk views, intervention recording.

---

## Security Notes

- **Student data is sensitive.** This system handles academic records of minors.
- **School-level isolation** is enforced: teachers can only access students from their school.
- **Roles** are stored as Firebase Custom Claims to prevent per-request Firestore lookups.
- **Tokens** are verified with `check_revoked=True` — revoked tokens are rejected immediately.
- **CORS** is restricted to configured origins — never use `*` in production.
- **Error details** are hidden in production via `HIDE_ERROR_DETAILS=true`.
- **Logs** never include tokens, private keys, or raw student records.

---

## Contributing

1. Follow the phase structure — do not implement Phase 2+ features in Phase 1 code.
2. All environment configuration goes through `app.core.config`.
3. All Firebase access goes through `app.core.firebase`.
4. All API responses use `app.utils.responses` helpers.
5. All protected routes use `Depends(get_current_user)` from `app.api.deps`.
