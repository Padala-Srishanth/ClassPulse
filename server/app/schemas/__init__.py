"""
app.schemas — API Request / Response Schemas

This package contains Pydantic schemas used specifically for API
serialisation/deserialisation — separate from domain models.

Separation from models/:
    models/  → Internal domain representation (what the app thinks about data)
    schemas/ → External API contract (what the API accepts and returns)

This separation allows the API contract to evolve independently from
internal representations, and makes versioning cleaner.

Phase 2 will add:
    - CreateStudentRequest / StudentResponse
    - CreateSchoolRequest / SchoolResponse
    - UploadDataRequest / UploadDataResponse

Phase 3 will add:
    - RiskSnapshotResponse
    - StudentRiskSummaryResponse

Phase 4 will add:
    - InterventionRequest / InterventionResponse
    - DashboardSummaryResponse
"""
