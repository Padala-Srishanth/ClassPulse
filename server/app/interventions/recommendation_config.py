"""
app.interventions.recommendation_config — Configurable Rules and Thresholds for Recommendations
"""

from __future__ import annotations
from typing import Dict
from pydantic import BaseModel, Field

from app.models.intervention import InterventionType


class RecommendationConfig(BaseModel):
    """Configuration thresholds for the deterministic recommendation engine."""

    # Triggering thresholds
    MIN_RISK_FOR_RECOMMENDATION: float = 20.0
    ATTENDANCE_DROP_THRESHOLD: float = 15.0      # 15 percentage points drop
    HOMEWORK_DROP_THRESHOLD: float = 20.0        # 20 percentage points drop
    ACADEMIC_DROP_THRESHOLD: float = 15.0        # 15 percentage points drop
    PERSISTENCE_WEEKS: int = 2                   # 2+ consecutive dropping weeks
    SUDDEN_DROP_THRESHOLD: float = 25.0          # 25+ percentage points drop
    STABLE_LOW_THRESHOLD: float = 55.0           # Baseline performance below 55%
    STABLE_LOW_MAX_DELTA: float = 8.0            # Fluctuation <= 8% considered stable
    RECOVERY_THRESHOLD_DELTA: float = 5.0        # Recent performance within 5% of baseline after a dip
    ESCALATION_OVERRIDE_DELTA: float = 25.0      # Risk jump >= 25 pts bypasses cooldown

    # Cooldown days after completion
    COOLDOWN_DAYS: Dict[str, int] = Field(
        default_factory=lambda: {
            InterventionType.ONE_ON_ONE_CHECKIN.value: 7,
            InterventionType.ONE_ON_ONE_SUPPORT.value: 7,
            InterventionType.PARENT_CONTACT.value: 14,
            InterventionType.ACADEMIC_SUPPORT.value: 14,
            InterventionType.COUNSELING_REFERRAL.value: 21,
            InterventionType.ATTENDANCE_SUPPORT.value: 14,
            InterventionType.EXTRA_ASSIGNMENT.value: 7,
            InterventionType.PEER_SUPPORT.value: 14,
            InterventionType.FOLLOW_UP_REVIEW.value: 7,
            InterventionType.OTHER.value: 7,
        }
    )

    # Suggested follow up duration
    DEFAULT_FOLLOW_UP_DAYS: int = 7
    ACADEMIC_FOLLOW_UP_DAYS: int = 14
    PARENT_CONTACT_FOLLOW_UP_DAYS: int = 14


# Singleton instance
recommendation_config = RecommendationConfig()
