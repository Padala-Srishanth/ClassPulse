# ClassPulse AI Assistant

A role-aware, natural-language chatbot layered on top of the existing ClassPulse
application for **teachers** and **principals/admins** only. It answers
questions about students, attendance, homework, test scores, risk, and
interventions using the data ClassPulse already has — nothing new is stored,
nothing existing is redesigned.

---

## 1. Purpose

ClassPulse already computes attendance percentages, homework completion,
academic performance, ML-driven risk scores, and intervention tracking. Today,
answering a question like *"Show me high-risk students with attendance below
75%"* means navigating multiple dashboards and manually cross-referencing
tables. The Assistant lets an authorized user simply **ask** — in plain
English — and get a concise, factual answer built entirely from verified
backend data.

## 2. Why teacher access is limited

Teachers work with the students in front of them. A teacher's assistant
scope is deliberately restricted to the classes where they appear in
`Class.teacher_ids` — the same field `app/api/v1/principal.py` already uses to
compute per-teacher assignments. This mirrors how the rest of the ClassPulse
API treats teachers (see `require_school_access` in `app/core/security.py`),
extended one level further: a teacher chatbot query is scoped to *class*, not
just *school*. A teacher can never use the assistant to see another
teacher's students, another class, or the whole school.

## 3. Why the principal is the primary use case

A principal already has school-wide visibility in the existing dashboards
(`app/api/v1/principal.py`); the assistant's value for a principal is
**speed and synthesis** — collapsing "open the attendance report, open the
academic report, open the risk dashboard, and manually intersect three
lists" into one sentence: *"Show students with attendance below 75% and
declining test scores."* Cross-category analysis (§7 below) is the flagship
capability, and it's only fully unlocked at school scope, which only a
principal/admin has.

## 4. Teacher capabilities

- Attendance: below/above a threshold, declining/improving trend, counts.
- Homework: not completed, frequently late, poor completion rate.
- Academic: declining/improving test scores, lowest performers.
- Risk: current risk level, why a student is high risk, risk trend.
- Individual student: a 360° summary (attendance + homework + academic +
  risk + interventions) for any student in their own classes.
- Cross-category questions within their own classes (e.g. "high-risk
  students with incomplete homework in my class").
- All of the above, always scoped to classes where they are listed in
  `teacher_ids`.

## 5. Principal / Admin capabilities

Everything a teacher can do, across every class in their school, plus:

- Cross-category analysis across the whole student body (§7).
- Per-class comparisons: *"Which class has the highest absenteeism?"*,
  *"Which class has the lowest average test performance?"*
- Per-class breakdowns: *"Show attendance trends by class."*
- Individual 360° student summaries for any student in the school.
- Intervention analysis: students with no intervention, ongoing
  interventions, overdue interventions, students who remain high-risk after
  a completed intervention.
- School-wide risk distribution and common risk factors.

## 6. Teacher limitations

A teacher's assistant is **read-only** and **class-scoped**. It cannot:

- See students/classes outside `teacher_ids` — asking for "the entire
  school" is met with: *"I can only provide information for the
  students/classes you are authorized to access."*
- Change any student record, risk score, or intervention.
- Change roles, permissions, or access credentials/secrets.
- Run arbitrary database queries or code — it only calls the fixed set of
  tools in `app/services/chatbot/tools.py`.

## 7. Principal limitations

A principal's assistant is also **read-only** and scoped to their own
school (`user.school_id`, or `school-001` as the existing ADMIN fallback —
see `app/api/v1/principal.py`). It cannot see another school's data, cannot
mutate records, and cannot execute arbitrary queries. It never re-runs the
ML risk pipeline (which writes new alerts) — it only reads the most recent,
already-persisted `RiskAlert`, exactly like `app/api/v1/risk.py`'s read
endpoints.

## 8. Cross-category analysis (the headline feature)

Example: *"Show students who have attendance below 75% and declining test
scores."* The orchestrator (`app/services/chatbot/orchestrator.py`):

1. Resolves the caller's authorized student list (`scope.py`).
2. Computes per-student metrics once (`tools.gather_metrics`): attendance %
   + trend, homework completion + trend, academic average + trend, current
   risk level/score, and intervention status.
3. Intersects every filter the question implied (attendance < 75% **AND**
   academic trend == DECLINING) over that same metric set.
4. Returns the matching students plus a plain-English summary.

This is why cross-category questions are cheap to add: every new filter is
just one more predicate over the same `StudentMetrics` list.

## 9. Individual Student 360° View

*"Give me a complete summary of Aman Verma."* → `get_student_summary()`
combines: student identity/class, attendance % + trend, homework completion
%, academic average + trend, current risk level/score/reasons (from the
existing `RiskAlert.reasons`, produced by `app/ml/explainability.py`), and
intervention history — one read-only call per underlying service, no new
computation of risk or grades.

## 10. Intervention analysis

`get_interventions()` reads `InterventionService` (student/class/school
scoped, matching existing service methods) and layers a few derived
read-only filters: `NONE` (no intervention on record), `ONGOING`
(`PLANNED`/`IN_PROGRESS`), `OVERDUE` (ongoing + `follow_up_date` in the
past), `COMPLETED`. The assistant never creates, edits, or deletes an
intervention — that remains the existing `InterventionModal` workflow in the
UI, which is untouched.

## 11. Architecture

```
Teacher / Principal
        |
Floating Chat Button  (ChatbotFloatingButton.tsx)
        |
Chat Panel            (ChatbotPanel.tsx, ChatbotWidget.tsx)
        |
Existing Firebase Auth (Authorization: Bearer <ID token>)
        |
FastAPI Chat Endpoint  (app/api/v1/chatbot.py)
        |
Role & Scope Authorization  (app/services/chatbot/scope.py)
        |
Chatbot Orchestrator   (app/services/chatbot/orchestrator.py)
        |
Intent / Filter Extraction (app/services/chatbot/nlu.py — deterministic, rule-based)
        |
Controlled ClassPulse Tools (app/services/chatbot/tools.py)
        |
Existing ClassPulse Services (Attendance/Homework/TestScore/Risk/Intervention/Class/Student)
        |
Firestore / Risk Engine (unchanged — read-only access to persisted RiskAlerts)
        |
Structured Results
        |
Response Generation (app/services/chatbot/responder.py — template, + optional LLM phrasing)
        |
Chat Panel (reply + suggestions)
```

See `docs/chatbot_architecture.drawio` for the diagram form of the above.

## 12. Authentication flow

Identical to every other ClassPulse endpoint: the frontend sends the
Firebase ID token (or, in local/demo mode, one of the existing `mock-*`
tokens already supported by `app/core/firebase.py::verify_firebase_token`)
in the `Authorization: Bearer <token>` header. `get_current_user`
(`app/core/security.py`) verifies it and produces a `CurrentUser` with
`role`/`school_id` taken from **Firebase custom claims** — never from
anything the client sends in the request body. The chatbot endpoints reuse
this dependency unmodified.

## 13. Authorization flow

1. `app/api/v1/chatbot.py::_require_chatbot_access` rejects anything that
   isn't `TEACHER` / `SCHOOL_ADMIN` / `ADMIN` with `403` before any Firestore
   read happens.
2. `scope.resolve_scope(user)` computes the authorized class list fresh, on
   every request, from the verified `CurrentUser` — teachers get classes
   where they're in `teacher_ids`; principals/admins get every class in
   their school.
3. Every tool call takes that `ChatScope` and calls
   `scope.require_class()` / `scope.require_student()` before touching data.
   Conversational context from a previous turn (`ChatContext`) can only
   **narrow** a query (e.g. restrict to a previously-returned student list)
   — it is never used to widen scope.
4. An out-of-scope request (a teacher asking for "the entire school", or
   naming a student outside their classes) gets a polite denial message,
   not an error — and not the requested data.

## 14. Tool architecture

`app/services/chatbot/tools.py` exposes exactly the functions named in the
spec, each read-only and scope-checked:

`get_student_summary`, `get_student_attendance`, `get_class_attendance`,
`get_students_below_attendance_threshold`, `get_homework_status`,
`get_student_test_scores`, `get_class_academic_performance`,
`get_student_risk`, `get_high_risk_students`, `get_risk_history`,
`get_interventions` (+ a couple of small helpers used for cross-category
filtering: `gather_metrics`, `find_students_by_query`,
`students_without_intervention`).

Every one of these calls an **existing** service
(`StudentService`, `AttendanceService`, `HomeworkService`,
`TestScoreService`, `RiskService`, `InterventionService`, `ClassService`) —
no Firestore collection is queried directly from the chatbot code, and no
business logic is duplicated.

## 15. Data retrieval flow

For a cross-category question, the orchestrator calls
`tools.gather_metrics(scope, candidates)` once, which — per student — reads
attendance, homework, test-score, latest risk alert, and intervention
records (bounded to `MAX_STUDENTS_PER_QUERY = 300` for a single request, a
sane cap for a school-sized dataset), then applies every requested filter as
an in-memory intersection over that one metrics list. Risk data is **always
read** (`RiskService.get_student_latest_alert` / `get_class_active_alerts`
/ `get_student_alert_history`) — the chatbot never triggers
`RiskService.analyze_student_risk` / `analyze_class_risk`, because those
**write** new alerts and trigger the intervention-recommendation engine as a
side effect. A chat question must never have a side effect.

## 16. LLM interaction

Per the spec: *"Do NOT rely on the LLM for deterministic calculations."*
Intent understanding, filter extraction, tool selection, authorization, and
every number in a reply are **100% deterministic Python** — see
`app/services/chatbot/nlu.py` (rule/keyword-based query understanding) and
`orchestrator.py` (routing + filtering). No external API key is required for
the assistant to be fully functional.

The **only** optional LLM usage is in `app/services/chatbot/responder.py`:
if `ANTHROPIC_API_KEY` is configured, the already-correct template reply and
its backing structured data are sent to the Anthropic Messages API with an
instruction to *rephrase, never invent*. Any failure (no key, timeout,
network error) silently falls back to the deterministic template — the
assistant's correctness never depends on the LLM being reachable.

## 17. Security architecture

- **Firebase ID token authentication** — reused as-is (`get_current_user`).
- **Backend role validation** — `_require_chatbot_access` in
  `app/api/v1/chatbot.py`; the frontend hiding the button for students is a
  UX nicety, never the enforcement point.
- **Teacher scope validation** — `scope.py`, derived from `Class.teacher_ids`.
- **Principal school-level validation** — scope is bounded to
  `user.school_id`; cross-school access is impossible even if a teacher/
  principal from another school reuses the same conversational `context`
  object (context never carries a school_id the server trusts).
- **School isolation** — enforced identically to the rest of the API,
  reusing the same `school_id` boundary as `require_school_access`.
- **Input validation** — Pydantic schemas (`app/schemas/chatbot.py`) bound
  message length (1–1000 chars) and validate context shape.
- **Safe error handling** — authorization/data errors return a friendly,
  non-leaking message (never a stack trace); unhandled exceptions fall
  through to the app's existing global exception handler.
- **No credentials/tokens in prompts** — the optional LLM call receives only
  already-authorized structured JSON and a draft sentence, never the
  Authorization header, Firebase claims, or any secret.
- **No unrestricted database access** — the LLM never sees Firestore; the
  rule-based orchestrator never runs a Firestore query outside the existing
  services.
- **No arbitrary code execution / arbitrary queries** — the tool set is a
  fixed, closed list of Python functions; there is no "run this query" or
  "eval this" capability anywhere in the pipeline.
- **Read-only** — no tool in `tools.py` calls `.set()`, `.update()`, or
  `.delete()` on any collection, and risk alerts are only ever read, never
  recomputed.

## 18. Example conversations

**Teacher, authorized:**
> **You:** Who has attendance below 75%?
> **Assistant:** There are 1 student(s) with attendance below 75% in your
> classes: Aman Verma.

**Teacher, unauthorized (whole-school):**
> **You:** Show all high-risk students in the entire school.
> **Assistant:** I can only provide information for the students/classes
> you are authorized to access.

**Principal, cross-category:**
> **You:** Show students who have attendance below 75% and declining test
> scores.
> **Assistant:** There are 1 student(s) below 75% attendance and with
> declining test scores across the school: Aman Verma.

**Principal, individual summary:**
> **You:** Give me a complete summary of "Aman Verma".
> **Assistant:** Summary for Aman Verma (Grade 10A): Attendance: 10%
> (declining). Homework completion: 66.7%. Academic average: 64%
> (declining). Risk level: HIGH (score 82.0). Risk factors: Attendance
> dropped sharply from baseline. 0 intervention(s) on record.

**Multi-turn:**
> **You:** Show high-risk students.
> **Assistant:** There are 2 student(s) high-risk across the school: Aman
> Verma, Ravi Kumar.
> **You:** Only Grade 10 Section A.
> **Assistant:** There are 1 student(s) high-risk in Grade 10 Section A:
> Aman Verma.
> **You:** Which of those have attendance below 75%?
> **Assistant:** There are 1 student(s) high-risk and with attendance below
> 75% in Grade 10 Section A: Aman Verma.

## 19. Technology stack

- **Backend:** FastAPI (existing app), Pydantic schemas, plain-Python rule
  engine for NLU — no new required Python dependency (the optional LLM
  phrasing pass reuses `httpx`, already a project dependency).
- **Frontend:** React + TypeScript (existing app), `lucide-react` icons
  (already a dependency) — no new npm packages.
- **Data:** existing Firestore collections via existing services — no new
  collections, no schema changes.
- **Optional LLM:** Anthropic Messages API (`claude-haiku-4-5-20251001` by
  default), used only for reply phrasing, gated behind `ANTHROPIC_API_KEY`.

## 20. Files added / modified

**Added (backend):**
- `server/app/schemas/chatbot.py`
- `server/app/services/chatbot/__init__.py`
- `server/app/services/chatbot/scope.py`
- `server/app/services/chatbot/nlu.py`
- `server/app/services/chatbot/tools.py`
- `server/app/services/chatbot/responder.py`
- `server/app/services/chatbot/orchestrator.py`
- `server/app/api/v1/chatbot.py`
- `server/tests/v1/test_chatbot.py`

**Modified (backend):**
- `server/app/api/router.py` — registered the `/api/v1/chatbot` router.
- `server/app/core/config.py` — added optional `ANTHROPIC_API_KEY` /
  `CHATBOT_LLM_MODEL` settings (both off/default unless explicitly set).

**Added (frontend):**
- `client/src/api/chatbot.ts`
- `client/src/components/chatbot/ChatbotFloatingButton.tsx`
- `client/src/components/chatbot/ChatbotPanel.tsx`
- `client/src/components/chatbot/ChatMessage.tsx`
- `client/src/components/chatbot/ChatInput.tsx`
- `client/src/components/chatbot/ChatbotWidget.tsx`

**Modified (frontend):**
- `client/src/App.tsx` — mounted `<ChatbotWidget />` as a fixed-position
  sibling next to the existing `TeacherLayout`/`PrincipalLayout` render
  branches only (never in the `StudentLayout` branch). No existing
  component, page, layout, or navigation item was changed.

**Docs:**
- `docs/CHATBOT.md` (this file)
- `docs/chatbot_architecture.drawio`

## 21. Known limitations of the rule-based NLU

The intent/filter parser (`nlu.py`) is intentionally deterministic
keyword/regex matching, not a general-purpose language model — this is a
deliberate security and correctness choice (see §16), not an oversight. It
robustly covers every example question in the product spec (see the test
suite and example conversations above) but, like any rule-based parser, can
miss unusual phrasings. When a question doesn't match a known pattern, the
assistant responds with a clear, honest out-of-scope message rather than
guessing.
