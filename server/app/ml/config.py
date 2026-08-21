"""
app.ml.config — ML & Risk Scoring Hyperparameters & Thresholds
"""

from pydantic import BaseModel, Field


class MLSettings(BaseModel):
    """Configurable hyperparameters for ClassPulse Risk Engine."""

    # Minimum history requirements
    min_history_weeks: int = Field(2, description="Minimum weeks of historical baseline required")
    min_attendance_records: int = Field(3, description="Minimum attendance records to assess attendance")
    min_homework_records: int = Field(2, description="Minimum homework assignments to assess homework")

    # Evaluation window (in weeks)
    recent_eval_window_weeks: int = Field(2, description="Recent window weeks to evaluate trend against baseline")

    # Signal Weights (sum to 1.0)
    weight_attendance: float = Field(0.35, description="Weight for attendance decline")
    weight_homework: float = Field(0.35, description="Weight for homework decline")
    weight_test: float = Field(0.30, description="Weight for test score decline")

    # Multipliers
    persistence_multiplier: float = Field(0.15, description="Boost when drop persists >= 2 weeks")
    cross_signal_multiplier: float = Field(0.20, description="Boost when multiple signals decline together")

    # Anomaly standard deviation multiplier (z-score threshold)
    z_score_threshold: float = Field(1.5, description="Z-score deviation threshold to flag as statistical anomaly")

    # Significant Drop Thresholds (percentage point drop from baseline)
    significant_drop_attendance: float = Field(15.0, description="Attendance drop % threshold for alert")
    significant_drop_homework: float = Field(20.0, description="Homework completion drop % threshold for alert")
    significant_drop_test: float = Field(15.0, description="Test score drop % threshold for alert")

    # Risk Categories Thresholds
    low_risk_max: float = Field(30.0, description="Upper bound for LOW risk (0-30)")
    medium_risk_max: float = Field(60.0, description="Upper bound for MEDIUM risk (31-60)")
    # 61-100 is HIGH risk

    # Model Version
    model_version: str = Field("risk-v1", description="Identifier of the risk model version")


ml_settings = MLSettings()
