"""
app.services — Business Logic Services

This package contains service classes and functions that implement
ClassPulse's business logic.

Services are:
  - Separate from routes (routes handle HTTP; services handle business logic)
  - Separate from models (services orchestrate; models represent data)
  - Independently testable without a running HTTP server
  - Injected into routes via FastAPI Depends()

Phase 2 will add:
    - StudentService    → Student CRUD, class assignment
    - SchoolService     → School management
    - IngestionService  → CSV parsing, validation, normalisation pipeline

Phase 3 will add:
    - BaselineService   → Student historical baseline computation
    - RiskService       → Trend detection, risk scoring, explainability
    - SchedulerService  → Weekly batch risk computation

Phase 4 will add:
    - InterventionService  → Recording and tracking teacher interventions
    - NotificationService  → Alert delivery (email, future WhatsApp)
"""
