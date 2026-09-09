"""
app.services.intervention_recommendation_service — Deterministic Smart Recommendation Engine
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.core.firebase import get_firestore_client
from app.core.logging import get_logger
from app.core.security import CurrentUser, require_school_access
from app.interventions.recommendation_config import recommendation_config
from app.ml.anomaly import AnomalyDetector
from app.ml.baseline import BaselineCalculator
from app.ml.explainability import ExplainabilityEngine
from app.ml.features import FeatureExtractor
from app.ml.scoring import RiskLevel, RiskScorer
from app.ml.trends import TrendAnalyzer
from app.models.intervention import (
    Intervention,
    InterventionStatus,
    InterventionType,
)
from app.models.intervention_recommendation import (
    DismissalReason,
    InterventionRecommendation,
    PriorityLevel,
    RecommendationReasonCode,
    RecommendationStatus,
)
from app.models.student import Student
from app.schemas.intervention import InterventionCreate
from app.services.attendance_service import AttendanceService
from app.services.class_service import ClassService
from app.services.homework_service import HomeworkService
from app.services.intervention_service import InterventionService
from app.services.monthly_report_service import MonthlyReportService
from app.services.student_service import StudentService
from app.services.test_score_service import TestScoreService

logger = get_logger(__name__)


class InterventionRecommendationService:
    @staticmethod
    def _collection():
        return get_firestore_client().collection("intervention_recommendations")

    # =========================================================================
    # Recommendation Generation & Analysis
    # =========================================================================

    @classmethod
    def analyze_student(cls, student_id: str) -> List[InterventionRecommendation]:
        """
        Analyze a single student and generate/update deterministic recommendations.
        """
        student = StudentService.get_student(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found.")

        return cls.generate_recommendations(student)

    @classmethod
    def generate_recommendations(
        cls,
        student: Student,
        risk_alert_id: Optional[str] = None,
        analysis_period_override: Optional[str] = None,
    ) -> List[InterventionRecommendation]:
        """
        Deterministic, rule-based recommendation generator.
        Evaluates signals, persistence, history, and previous interventions.
        """
        # 1. Fetch raw academic records
        attendance_records = AttendanceService.list_student_attendance(student.id, limit=500)
        homework_records = HomeworkService.list_student_homework(student.id, limit=500)
        test_records = TestScoreService.list_student_test_scores(student.id, limit=500)

        # 2. Extract signatures, baseline, trends, anomaly, risk score
        signatures = FeatureExtractor.build_weekly_signatures(
            attendance_records=attendance_records,
            homework_records=homework_records,
            test_records=test_records,
        )

        analysis_period = analysis_period_override or (
            signatures[-1].week_key if signatures else datetime.now(tz=timezone.utc).strftime("%Y-W%U")
        )

        baseline, baseline_sigs, recent_sigs = BaselineCalculator.calculate_baseline(signatures)
        trends = TrendAnalyzer.analyze_trends(baseline, recent_sigs)
        anomaly = AnomalyDetector.detect_anomalies(baseline, trends)
        score_output = RiskScorer.compute_risk(baseline, trends, anomaly)

        # Retrieve class info for descriptive display
        class_obj = ClassService.get_class(student.class_id)
        class_name = class_obj.name if class_obj else f"Grade {student.grade}-{student.section}"

        # Retrieve student monthly report history to inspect multi-month persistence or recovery
        monthly_reports = MonthlyReportService.list_student_report_history(student.id)

        # Retrieve previous interventions
        existing_interventions = InterventionService.list_student_interventions(student.id, limit=100)

        # 3. Evaluate Rule 9: Insufficient Data
        if not baseline.has_sufficient_history or score_output.risk_level == RiskLevel.INSUFFICIENT_DATA:
            rec = cls._create_insufficient_data_recommendation(
                student=student,
                class_name=class_name,
                period=analysis_period,
                risk_alert_id=risk_alert_id,
            )
            saved = cls._persist_recommendation(rec)
            return [saved]

        # 4. Check for Rule 7: Temporary Dip & Recovery
        is_recovery = cls._detect_recovery(signatures, monthly_reports, score_output)
        if is_recovery:
            rec = cls._create_recovery_recommendation(
                student=student,
                class_name=class_name,
                period=analysis_period,
                risk_alert_id=risk_alert_id,
                score_output=score_output,
            )
            saved = cls._persist_recommendation(rec)
            return [saved]

        # 5. Check for Rule 8: Naturally Low but Stable Performance
        is_stable_low = cls._detect_stable_low(baseline, trends, score_output)
        if is_stable_low:
            recs = cls._create_stable_low_recommendations(
                student=student,
                class_name=class_name,
                period=analysis_period,
                risk_alert_id=risk_alert_id,
                baseline=baseline,
                trends=trends,
                score_output=score_output,
            )
            saved_recs = [cls._persist_recommendation(r) for r in recs]
            return cls._rank_recommendations(saved_recs)

        # 6. Evaluate Decline Signals
        candidates = cls._evaluate_decline_rules(
            student=student,
            class_name=class_name,
            period=analysis_period,
            risk_alert_id=risk_alert_id,
            baseline=baseline,
            trends=trends,
            score_output=score_output,
            test_records=test_records,
            monthly_reports=monthly_reports,
        )

        if not candidates:
            # Student is stable and high-performing (e.g. Student A)
            return []

        # 7. Apply Previous Intervention Inspection & Cooldown Logic
        filtered_candidates = cls._apply_intervention_history_and_cooldown(
            candidates=candidates,
            existing_interventions=existing_interventions,
            current_risk_score=score_output.risk_score,
            student=student,
            class_name=class_name,
            period=analysis_period,
        )

        # 8. Rank and Persist
        ranked = cls._rank_recommendations(filtered_candidates)
        persisted = [cls._persist_recommendation(r) for r in ranked]
        return persisted

    # =========================================================================
    # Rule Evaluation Methods
    # =========================================================================

    @classmethod
    def _detect_recovery(
        cls,
        signatures: list,
        monthly_reports: list,
        score_output: Any,
    ) -> bool:
        """
        Rule 7: Detect if student had a dip in a prior evaluation period but has now recovered.
        """
        # Check monthly history for prior dip followed by recovery
        if len(monthly_reports) >= 2:
            prev_risk = monthly_reports[-2].risk.get("risk_score", 0) if monthly_reports[-2].risk else 0
            curr_risk = score_output.risk_score
            if prev_risk >= 60.0 and curr_risk <= 35.0:
                return True

        # Check weekly signatures: prior 2-3 weeks had dip, recent week improved close to baseline
        if len(signatures) >= 3:
            recent_sig = signatures[-1]
            prior_sig = signatures[-2]
            if (
                prior_sig.attendance_rate is not None
                and recent_sig.attendance_rate is not None
                and prior_sig.attendance_rate < 70.0
                and recent_sig.attendance_rate >= 85.0
                and score_output.risk_score <= 30.0
            ):
                return True

        return False

    @classmethod
    def _detect_stable_low(
        cls,
        baseline: Any,
        trends: Any,
        score_output: Any,
    ) -> bool:
        """
        Rule 8: Detect if student is naturally low performing but stable over time.
        Distinguish from sudden/sharp declines.
        """
        base_test = baseline.baseline_test_average or 100.0
        base_hw = baseline.baseline_homework_completion_rate or 100.0
        test_delta = abs(trends.test_delta or 0.0)
        hw_delta = abs(trends.homework_delta or 0.0)

        is_low = (
            base_test <= recommendation_config.STABLE_LOW_THRESHOLD
            or base_hw <= recommendation_config.STABLE_LOW_THRESHOLD
        )
        is_stable = (
            test_delta <= recommendation_config.STABLE_LOW_MAX_DELTA
            and hw_delta <= recommendation_config.STABLE_LOW_MAX_DELTA
        )

        return is_low and is_stable

    @classmethod
    def _evaluate_decline_rules(
        cls,
        student: Student,
        class_name: str,
        period: str,
        risk_alert_id: Optional[str],
        baseline: Any,
        trends: Any,
        score_output: Any,
        test_records: list,
        monthly_reports: list,
    ) -> List[InterventionRecommendation]:
        """
        Evaluate Rules 1 to 6.
        """
        cfg = recommendation_config
        att_drop = abs(min(0.0, trends.attendance_delta)) if trends.attendance_delta is not None else 0.0
        hw_drop = abs(min(0.0, trends.homework_delta)) if trends.homework_delta is not None else 0.0
        test_drop = abs(min(0.0, trends.test_delta)) if trends.test_delta is not None else 0.0

        is_att_drop = att_drop >= cfg.ATTENDANCE_DROP_THRESHOLD or (trends.is_attendance_declining and att_drop >= 10.0)
        is_hw_drop = hw_drop >= cfg.HOMEWORK_DROP_THRESHOLD or (trends.is_homework_declining and hw_drop >= 12.0)
        is_test_drop = test_drop >= cfg.ACADEMIC_DROP_THRESHOLD or (trends.is_test_declining and test_drop >= 10.0)

        declining_count = sum(1 for flag in (is_att_drop, is_hw_drop, is_test_drop) if flag)
        is_persistent = (
            trends.consecutive_dropping_weeks >= cfg.PERSISTENCE_WEEKS
            or (len(monthly_reports) >= 2 and all(r.risk.get("risk_score", 0) >= 50 for r in monthly_reports[-2:]))
        )
        is_sudden_drop = (
            att_drop >= cfg.SUDDEN_DROP_THRESHOLD
            or hw_drop >= cfg.SUDDEN_DROP_THRESHOLD
            or test_drop >= cfg.SUDDEN_DROP_THRESHOLD
        )

        # If student has low risk and no significant drops, return empty
        if score_output.risk_score < cfg.MIN_RISK_FOR_RECOMMENDATION and declining_count == 0:
            return []

        # Calculate Priority Score (0-100)
        base_priority = score_output.risk_score
        bonus = (declining_count * 8.0) + (15.0 if is_persistent else 0.0) + (15.0 if is_sudden_drop else 0.0)
        priority_score = round(min(100.0, max(20.0, base_priority + bonus)), 1)
        priority_level = cls._determine_priority_level(priority_score)

        signals_summary = {
            "attendance_drop": round(att_drop, 1),
            "homework_drop": round(hw_drop, 1),
            "academic_drop": round(test_drop, 1),
            "declining_signals_count": declining_count,
            "is_persistent": is_persistent,
            "is_sudden_drop": is_sudden_drop,
            "recent_attendance": trends.recent_attendance_rate,
            "baseline_attendance": baseline.baseline_attendance_rate,
            "recent_homework": trends.recent_homework_completion_rate,
            "baseline_homework": baseline.baseline_homework_completion_rate,
            "recent_test": trends.recent_test_average,
            "baseline_test": baseline.baseline_test_average,
        }

        recommendations: List[InterventionRecommendation] = []
        now = datetime.now(tz=timezone.utc)

        # ---------------------------------------------------------------------
        # Rule 4: Multi-Signal Decline (2 or more declining signals)
        # ---------------------------------------------------------------------
        if declining_count >= 2:
            reason_codes = [RecommendationReasonCode.MULTI_SIGNAL_DECLINE.value]
            if is_persistent:
                reason_codes.append(RecommendationReasonCode.PERSISTENT_DECLINE.value)
            if is_sudden_drop:
                reason_codes.append(RecommendationReasonCode.SUDDEN_DROP.value)

            decline_phrases = []
            if is_att_drop:
                decline_phrases.append(f"attendance decreased from {baseline.baseline_attendance_rate:.0f}% to {trends.recent_attendance_rate:.0f}% ({att_drop:.0f}% drop)")
            if is_hw_drop:
                decline_phrases.append(f"homework completion dropped from {baseline.baseline_homework_completion_rate:.0f}% to {trends.recent_homework_completion_rate:.0f}% ({hw_drop:.0f}% drop)")
            if is_test_drop:
                decline_phrases.append(f"academic test performance fell from {baseline.baseline_test_average:.0f}% to {trends.recent_test_average:.0f}% ({test_drop:.0f}% drop)")

            multi_exp = (
                f"Multiple major risk signals are declining simultaneously: {'; '.join(decline_phrases)}."
                + (f" Decline has persisted across {trends.consecutive_dropping_weeks} consecutive evaluation periods." if is_persistent else "")
                + (" Significant sudden drop detected compared to historical baseline." if is_sudden_drop else "")
            )

            # Priority 1: ONE_ON_ONE_CHECKIN
            p1_score = priority_score
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.ONE_ON_ONE_CHECKIN.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.ONE_ON_ONE_CHECKIN,
                    priority_level=priority_level,
                    priority_score=p1_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=multi_exp,
                    recommended_actions=[
                        "Schedule an immediate one-on-one conference to discuss holistic barriers.",
                        "Establish structured attendance and study goals for the coming 7 days.",
                        "Schedule a 7-day follow-up checkpoint to measure initial recovery.",
                    ],
                    suggested_follow_up_days=cfg.DEFAULT_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

            # Priority 2: ACADEMIC_SUPPORT
            p2_score = round(max(20.0, priority_score - 10.0), 1)
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.ACADEMIC_SUPPORT.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.ACADEMIC_SUPPORT,
                    priority_level=cls._determine_priority_level(p2_score),
                    priority_score=p2_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=f"Academic reinforcement needed alongside check-in. {multi_exp}",
                    recommended_actions=[
                        "Enroll student into guided study or remedial subject clinic.",
                        "Provide structured review worksheets targeting identified weak topics.",
                        "Review progress after two weeks.",
                    ],
                    suggested_follow_up_days=cfg.ACADEMIC_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

            # Priority 3: PARENT_CONTACT
            p3_score = round(max(20.0, priority_score - 18.0), 1)
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.PARENT_CONTACT.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.PARENT_CONTACT,
                    priority_level=cls._determine_priority_level(p3_score),
                    priority_score=p3_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=f"Coordinated parent consultation advised to align home and school support. {multi_exp}",
                    recommended_actions=[
                        "Contact guardian via telephone to share attendance and academic observations.",
                        "Align on homework routine and attendance expectations.",
                        "Plan a 14-day progress follow-up with the family.",
                    ],
                    suggested_follow_up_days=cfg.PARENT_CONTACT_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

            # Priority 4: COUNSELING_REFERRAL (neutral phrasing)
            p4_score = round(max(20.0, priority_score - 28.0), 1)
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.COUNSELING_REFERRAL.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.COUNSELING_REFERRAL,
                    priority_level=cls._determine_priority_level(p4_score),
                    priority_score=p4_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation="Multi-signal decline observed across academic and engagement indicators. Consider appropriate student support or counseling resources according to school policy.",
                    recommended_actions=[
                        "Consult with school counseling or student welfare coordinator as appropriate.",
                        "Assess if non-academic personal or environmental barriers exist.",
                        "Follow standard institutional welfare escalation protocol.",
                    ],
                    suggested_follow_up_days=cfg.DEFAULT_FOLLOW_UP_DAYS * 2,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

            return recommendations

        # ---------------------------------------------------------------------
        # Rule 1: Attendance Decline
        # ---------------------------------------------------------------------
        if is_att_drop:
            reason_codes = [RecommendationReasonCode.ATTENDANCE_DROP.value]
            if is_persistent:
                reason_codes.append(RecommendationReasonCode.PERSISTENT_DECLINE.value)
            if is_sudden_drop:
                reason_codes.append(RecommendationReasonCode.SUDDEN_DROP.value)

            att_exp = (
                f"Attendance decreased from {baseline.baseline_attendance_rate:.0f}% historical baseline to {trends.recent_attendance_rate:.0f}% recently ({att_drop:.0f}% drop)"
                + (f" and the decline persisted across {trends.consecutive_dropping_weeks} consecutive weeks." if is_persistent else ".")
                + (" Significant sudden drop detected compared with historical baseline." if is_sudden_drop else "")
            )

            # Priority 1: ONE_ON_ONE_CHECKIN
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.ONE_ON_ONE_CHECKIN.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.ONE_ON_ONE_CHECKIN,
                    priority_level=priority_level,
                    priority_score=priority_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=att_exp,
                    recommended_actions=[
                        "Meet the student privately to understand attendance hurdles.",
                        "Set an attendance target for the next 7 days.",
                        "Monitor daily attendance in the morning register.",
                    ],
                    suggested_follow_up_days=cfg.DEFAULT_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

            # Priority 2: ATTENDANCE_SUPPORT
            p2_score = round(max(20.0, priority_score - 10.0), 1)
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.ATTENDANCE_SUPPORT.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.ATTENDANCE_SUPPORT,
                    priority_level=cls._determine_priority_level(p2_score),
                    priority_score=p2_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=f"Dedicated attendance monitoring recommended. {att_exp}",
                    recommended_actions=[
                        "Pair student with an attendance buddy or mentor in class.",
                        "Track a daily morning arrival log for 7 to 14 days.",
                        "Acknowledge weekly streak milestones.",
                    ],
                    suggested_follow_up_days=cfg.DEFAULT_FOLLOW_UP_DAYS * 2,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

            # Priority 3: PARENT_CONTACT
            p3_score = round(max(20.0, priority_score - 20.0), 1)
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.PARENT_CONTACT.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.PARENT_CONTACT,
                    priority_level=cls._determine_priority_level(p3_score),
                    priority_score=p3_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=f"Parent communication recommended if attendance hurdles persist. {att_exp}",
                    recommended_actions=[
                        "Inform parent or guardian regarding unexcused absences.",
                        "Verify transportation or health factors affecting morning punctuality.",
                        "Follow up after 14 days.",
                    ],
                    suggested_follow_up_days=cfg.PARENT_CONTACT_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

        # ---------------------------------------------------------------------
        # Rule 2: Homework Decline
        # ---------------------------------------------------------------------
        if is_hw_drop:
            reason_codes = [RecommendationReasonCode.HOMEWORK_DROP.value]
            if is_persistent:
                reason_codes.append(RecommendationReasonCode.PERSISTENT_DECLINE.value)
            if is_sudden_drop:
                reason_codes.append(RecommendationReasonCode.SUDDEN_DROP.value)

            hw_exp = (
                f"Homework completion decreased from {baseline.baseline_homework_completion_rate:.0f}% to {trends.recent_homework_completion_rate:.0f}% across recent evaluation weeks ({hw_drop:.0f}% drop)."
                + (f" Decline persisted across {trends.consecutive_dropping_weeks} consecutive evaluation periods." if is_persistent else "")
            )

            # Priority 1: ONE_ON_ONE_CHECKIN
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.ONE_ON_ONE_CHECKIN.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.ONE_ON_ONE_CHECKIN,
                    priority_level=priority_level,
                    priority_score=priority_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=hw_exp,
                    recommended_actions=[
                        "Discuss assignment hurdles and study routine directly with student.",
                        "Clarify upcoming deadlines and submission expectations.",
                        "Review progress after one week.",
                    ],
                    suggested_follow_up_days=cfg.DEFAULT_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

            # Priority 2: EXTRA_ASSIGNMENT
            p2_score = round(max(20.0, priority_score - 10.0), 1)
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.EXTRA_ASSIGNMENT.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.EXTRA_ASSIGNMENT,
                    priority_level=cls._determine_priority_level(p2_score),
                    priority_score=p2_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=f"Remedial assignment recommended to bridge missing homework submissions. {hw_exp}",
                    recommended_actions=[
                        "Assign manageable remedial coursework to compensate for missing tasks.",
                        "Provide guided hints or practice problems.",
                        "Set milestone check on submission after 7 days.",
                    ],
                    suggested_follow_up_days=cfg.DEFAULT_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

            # Priority 3: ACADEMIC_SUPPORT
            p3_score = round(max(20.0, priority_score - 18.0), 1)
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.ACADEMIC_SUPPORT.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.ACADEMIC_SUPPORT,
                    priority_level=cls._determine_priority_level(p3_score),
                    priority_score=p3_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=f"Guided academic support advised to help student regain homework momentum. {hw_exp}",
                    recommended_actions=[
                        "Offer teacher or peer-led after-school study group assistance.",
                        "Ensure textbook and worksheet access is readily available.",
                        "Check homework completion at the start of each class.",
                    ],
                    suggested_follow_up_days=cfg.ACADEMIC_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

        # ---------------------------------------------------------------------
        # Rule 3: Academic Performance Decline
        # ---------------------------------------------------------------------
        if is_test_drop:
            reason_codes = [RecommendationReasonCode.ACADEMIC_DROP.value]
            if is_persistent:
                reason_codes.append(RecommendationReasonCode.PERSISTENT_DECLINE.value)
            if is_sudden_drop:
                reason_codes.append(RecommendationReasonCode.SUDDEN_DROP.value)

            # Detect weak subjects
            weak_subjects = cls._find_weak_subjects(test_records)
            subject_clause = f" {', '.join(weak_subjects)} show the strongest decline." if weak_subjects else ""

            acad_exp = (
                f"Average assessment performance dropped from {baseline.baseline_test_average:.0f}% to {trends.recent_test_average:.0f}% ({test_drop:.0f}% drop).{subject_clause}"
                + (f" Decline persisted across {trends.consecutive_dropping_weeks} consecutive evaluation periods." if is_persistent else "")
                + (" Significant sudden decline detected compared with historical baseline." if is_sudden_drop else "")
            )

            # Priority 1: ACADEMIC_SUPPORT
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.ACADEMIC_SUPPORT.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.ACADEMIC_SUPPORT,
                    priority_level=priority_level,
                    priority_score=priority_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=acad_exp,
                    recommended_actions=[
                        f"Provide targeted remedial coaching{' in ' + ', '.join(weak_subjects) if weak_subjects else ''}.",
                        "Review recent examination mistakes and reinforce foundational concepts.",
                        "Re-assess concept mastery with a brief formative quiz in 14 days.",
                    ],
                    suggested_follow_up_days=cfg.ACADEMIC_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

            # Priority 2: ONE_ON_ONE_CHECKIN
            p2_score = round(max(20.0, priority_score - 10.0), 1)
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.ONE_ON_ONE_CHECKIN.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.ONE_ON_ONE_CHECKIN,
                    priority_level=cls._determine_priority_level(p2_score),
                    priority_score=p2_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=f"One-on-one academic consultation recommended. {acad_exp}",
                    recommended_actions=[
                        "Review exam answer scripts directly with the student.",
                        "Clarify misunderstandings and study techniques.",
                        "Set concrete target score for next test.",
                    ],
                    suggested_follow_up_days=cfg.DEFAULT_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

            # Priority 3: EXTRA_ASSIGNMENT
            p3_score = round(max(20.0, priority_score - 20.0), 1)
            recommendations.append(
                InterventionRecommendation(
                    recommendation_id=f"rec_{student.id}_{period}_{InterventionType.EXTRA_ASSIGNMENT.value}",
                    school_id=student.school_id,
                    student_id=student.id,
                    student_name=student.name,
                    class_id=student.class_id,
                    class_name=class_name,
                    risk_alert_id=risk_alert_id,
                    report_period=period,
                    recommendation_type=InterventionType.EXTRA_ASSIGNMENT,
                    priority_level=cls._determine_priority_level(p3_score),
                    priority_score=p3_score,
                    status=RecommendationStatus.PENDING,
                    reason_codes=reason_codes,
                    explanation=f"Targeted practice coursework recommended. {acad_exp}",
                    recommended_actions=[
                        f"Assign focused practice problem sets{' in ' + ', '.join(weak_subjects) if weak_subjects else ''}.",
                        "Review student answers and provide written feedback within 7 days.",
                    ],
                    suggested_follow_up_days=cfg.DEFAULT_FOLLOW_UP_DAYS,
                    signals_summary=signals_summary,
                    risk_score=score_output.risk_score,
                    risk_level=score_output.risk_level.value,
                    created_at=now,
                    updated_at=now,
                )
            )

        return recommendations

    @classmethod
    def _create_insufficient_data_recommendation(
        cls,
        student: Student,
        class_name: str,
        period: str,
        risk_alert_id: Optional[str],
    ) -> InterventionRecommendation:
        """Rule 9: Insufficient Data."""
        now = datetime.now(tz=timezone.utc)
        return InterventionRecommendation(
            recommendation_id=f"rec_{student.id}_{period}_{InterventionType.OTHER.value}",
            school_id=student.school_id,
            student_id=student.id,
            student_name=student.name,
            class_id=student.class_id,
            class_name=class_name,
            risk_alert_id=risk_alert_id,
            report_period=period,
            recommendation_type=InterventionType.OTHER,
            priority_level=PriorityLevel.LOW,
            priority_score=15.0,
            status=RecommendationStatus.PENDING,
            reason_codes=[RecommendationReasonCode.INSUFFICIENT_DATA.value],
            explanation="Collect additional attendance and academic data before making a risk-based intervention decision.",
            recommended_actions=[
                "Log daily attendance consistently for at least two consecutive weeks.",
                "Record homework completion marks and classroom participation.",
                "Ensure assessment scores are submitted before applying risk interventions.",
            ],
            suggested_follow_up_days=14,
            signals_summary={"data_status": "NEEDS_DATA"},
            risk_score=0.0,
            risk_level=RiskLevel.INSUFFICIENT_DATA.value,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def _create_recovery_recommendation(
        cls,
        student: Student,
        class_name: str,
        period: str,
        risk_alert_id: Optional[str],
        score_output: Any,
    ) -> InterventionRecommendation:
        """Rule 7: Temporary Dip followed by Recovery."""
        now = datetime.now(tz=timezone.utc)
        return InterventionRecommendation(
            recommendation_id=f"rec_{student.id}_{period}_{InterventionType.FOLLOW_UP_REVIEW.value}",
            school_id=student.school_id,
            student_id=student.id,
            student_name=student.name,
            class_id=student.class_id,
            class_name=class_name,
            risk_alert_id=risk_alert_id,
            report_period=period,
            recommendation_type=InterventionType.FOLLOW_UP_REVIEW,
            priority_level=PriorityLevel.LOW,
            priority_score=20.0,
            status=RecommendationStatus.PENDING,
            reason_codes=[RecommendationReasonCode.RECOVERY_DETECTED.value],
            explanation="Student experienced a temporary dip in previous evaluations but has since recovered toward historical baseline. Continue monitoring without aggressive interventions.",
            recommended_actions=[
                "Continue standard weekly monitoring of attendance and coursework.",
                "Provide verbal positive reinforcement for sustained improvement.",
                "No parent contact or formal escalation required at this time.",
            ],
            suggested_follow_up_days=14,
            signals_summary={"recovery_detected": True},
            risk_score=score_output.risk_score,
            risk_level=score_output.risk_level.value,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def _create_stable_low_recommendations(
        cls,
        student: Student,
        class_name: str,
        period: str,
        risk_alert_id: Optional[str],
        baseline: Any,
        trends: Any,
        score_output: Any,
    ) -> List[InterventionRecommendation]:
        """
        Rule 8: Naturally Low but Stable Performance.
        Supportive rather than urgent. Never HIGH or URGENT.
        """
        now = datetime.now(tz=timezone.utc)
        b_test = baseline.baseline_test_average or 50.0
        r_test = trends.recent_test_average or 50.0
        base_exp = f"Performance is consistently below the desired academic threshold (baseline {b_test:.0f}%, recent {r_test:.0f}%) but remains stable rather than experiencing a sudden drop."

        rec1 = InterventionRecommendation(
            recommendation_id=f"rec_{student.id}_{period}_{InterventionType.ACADEMIC_SUPPORT.value}",
            school_id=student.school_id,
            student_id=student.id,
            student_name=student.name,
            class_id=student.class_id,
            class_name=class_name,
            risk_alert_id=risk_alert_id,
            report_period=period,
            recommendation_type=InterventionType.ACADEMIC_SUPPORT,
            priority_level=PriorityLevel.MEDIUM,
            priority_score=50.0,  # Capped below HIGH threshold (70)
            status=RecommendationStatus.PENDING,
            reason_codes=[RecommendationReasonCode.STABLE_LOW_PERFORMANCE.value],
            explanation=base_exp,
            recommended_actions=[
                "Provide ongoing supportive remedial exercises during designated study periods.",
                "Focus on core foundational competency benchmarks.",
                "Review academic progress at end of evaluation month.",
            ],
            suggested_follow_up_days=recommendation_config.ACADEMIC_FOLLOW_UP_DAYS,
            signals_summary={"is_stable_low": True, "baseline_test": b_test, "recent_test": r_test},
            risk_score=score_output.risk_score,
            risk_level=score_output.risk_level.value,
            created_at=now,
            updated_at=now,
        )

        rec2 = InterventionRecommendation(
            recommendation_id=f"rec_{student.id}_{period}_{InterventionType.EXTRA_ASSIGNMENT.value}",
            school_id=student.school_id,
            student_id=student.id,
            student_name=student.name,
            class_id=student.class_id,
            class_name=class_name,
            risk_alert_id=risk_alert_id,
            report_period=period,
            recommendation_type=InterventionType.EXTRA_ASSIGNMENT,
            priority_level=PriorityLevel.LOW,
            priority_score=35.0,
            status=RecommendationStatus.PENDING,
            reason_codes=[RecommendationReasonCode.STABLE_LOW_PERFORMANCE.value],
            explanation=f"Optional manageable practice assignments to bolster comprehension. {base_exp}",
            recommended_actions=[
                "Assign bite-sized, structured practice sheets to build confidence.",
                "Praise consistent completion.",
            ],
            suggested_follow_up_days=recommendation_config.DEFAULT_FOLLOW_UP_DAYS,
            signals_summary={"is_stable_low": True},
            risk_score=score_output.risk_score,
            risk_level=score_output.risk_level.value,
            created_at=now,
            updated_at=now,
        )

        return [rec1, rec2]

    # =========================================================================
    # Previous Interventions & Cooldown Filter
    # =========================================================================

    @classmethod
    def _apply_intervention_history_and_cooldown(
        cls,
        candidates: List[InterventionRecommendation],
        existing_interventions: List[Intervention],
        current_risk_score: float,
        student: Student,
        class_name: str,
        period: str,
    ) -> List[InterventionRecommendation]:
        """
        Inspect existing interventions:
        1. Avoid duplicate if PLANNED or IN_PROGRESS -> recommend FOLLOW_UP_REVIEW instead.
        2. Respect cooldown window for COMPLETED interventions -> suppress unless significant escalation.
        """
        cfg = recommendation_config
        now = datetime.now(tz=timezone.utc)
        filtered: List[InterventionRecommendation] = []
        already_added_types = set()

        for cand in candidates:
            rec_type = cand.recommendation_type.value

            # Find matching existing interventions
            active_matching = [
                i for i in existing_interventions
                if (i.type.value == rec_type or (rec_type == "ONE_ON_ONE_CHECKIN" and i.type.value == "ONE_ON_ONE_SUPPORT"))
                and i.status in (InterventionStatus.PLANNED, InterventionStatus.IN_PROGRESS)
            ]

            if active_matching:
                # Active intervention exists: do NOT create duplicate!
                # Recommend FOLLOW_UP_REVIEW instead if not already present
                if InterventionType.FOLLOW_UP_REVIEW.value not in already_added_types:
                    active_int = active_matching[0]
                    follow_up = InterventionRecommendation(
                        recommendation_id=f"rec_{student.id}_{period}_{InterventionType.FOLLOW_UP_REVIEW.value}",
                        school_id=student.school_id,
                        student_id=student.id,
                        student_name=student.name,
                        class_id=student.class_id,
                        class_name=class_name,
                        risk_alert_id=cand.risk_alert_id,
                        report_period=period,
                        recommendation_type=InterventionType.FOLLOW_UP_REVIEW,
                        priority_level=cand.priority_level,
                        priority_score=cand.priority_score,
                        status=RecommendationStatus.PENDING,
                        reason_codes=cand.reason_codes + ["ACTIVE_INTERVENTION_IN_PROGRESS"],
                        explanation=f"A {rec_type.replace('_', ' ')} intervention is currently in progress (Status: {active_int.status.value}). Follow up and monitor existing action plan before creating duplicate interventions.",
                        recommended_actions=[
                            f"Check progress on active intervention created on {active_int.created_at.strftime('%Y-%m-%d')}.",
                            "Assess student response and record milestone notes.",
                            "Mark active intervention completed when target outcome is achieved.",
                        ],
                        suggested_follow_up_days=cfg.DEFAULT_FOLLOW_UP_DAYS,
                        signals_summary=cand.signals_summary,
                        risk_score=cand.risk_score,
                        risk_level=cand.risk_level,
                        created_at=now,
                        updated_at=now,
                    )
                    filtered.append(follow_up)
                    already_added_types.add(InterventionType.FOLLOW_UP_REVIEW.value)
                continue

            # Check Cooldown for recently completed interventions
            completed_matching = [
                i for i in existing_interventions
                if (i.type.value == rec_type or (rec_type == "ONE_ON_ONE_CHECKIN" and i.type.value == "ONE_ON_ONE_SUPPORT"))
                and i.status == InterventionStatus.COMPLETED
            ]

            if completed_matching:
                completed_matching.sort(key=lambda i: i.updated_at, reverse=True)
                latest = completed_matching[0]
                days_since = (now - latest.updated_at).days
                cooldown_days = cfg.COOLDOWN_DAYS.get(rec_type, 7)

                if days_since < cooldown_days:
                    # Within cooldown window. Check for significant escalation
                    is_escalated = (
                        cand.priority_level == PriorityLevel.URGENT
                        or current_risk_score >= 80.0
                    )
                    if not is_escalated:
                        # Cooldown applies: suppress repeat recommendation
                        logger.info(
                            "Suppressing %s recommendation for student %s: completed %d days ago (cooldown %d days).",
                            rec_type,
                            student.id,
                            days_since,
                            cooldown_days,
                        )
                        continue
                    else:
                        cand.explanation += f" (Note: Recommended during standard {cooldown_days}-day cooldown due to significant risk escalation)."

            if rec_type not in already_added_types:
                filtered.append(cand)
                already_added_types.add(rec_type)

        return filtered

    # =========================================================================
    # Helpers: Scoring, Weak Subjects, Sorting
    # =========================================================================

    @staticmethod
    def _determine_priority_level(score: float) -> PriorityLevel:
        if score >= 85.0:
            return PriorityLevel.URGENT
        elif score >= 70.0:
            return PriorityLevel.HIGH
        elif score >= 40.0:
            return PriorityLevel.MEDIUM
        return PriorityLevel.LOW

    @staticmethod
    def _find_weak_subjects(test_records: list) -> List[str]:
        """Group test scores by subject and find subjects with lowest averages."""
        if not test_records:
            return []
        subject_scores: Dict[str, List[float]] = {}
        for r in test_records:
            sub = r.subject or "General"
            max_s = getattr(r, "max_score", None) or getattr(r, "max_marks", None) or 100.0
            if max_s > 0:
                pct = (r.score / max_s) * 100.0
                subject_scores.setdefault(sub, []).append(pct)

        averages = {
            sub: (sum(scores) / len(scores))
            for sub, scores in subject_scores.items()
        }
        sorted_subjects = sorted(averages.items(), key=lambda x: x[1])
        weak = [s for s, avg in sorted_subjects if avg < 65.0]
        return weak[:2]

    @classmethod
    def _rank_recommendations(
        cls, recommendations: List[InterventionRecommendation]
    ) -> List[InterventionRecommendation]:
        """Rank recommendations by priority_score DESC."""
        return sorted(recommendations, key=lambda r: r.priority_score, reverse=True)

    # =========================================================================
    # Persistence & Queries
    # =========================================================================

    @classmethod
    def _persist_recommendation(
        cls, rec: InterventionRecommendation
    ) -> InterventionRecommendation:
        """
        Persist recommendation in Firestore with deterministic document ID.
        If a PENDING recommendation of the same ID already exists, update its values
        to avoid creating duplicate pending entries on repeated analysis.
        """
        doc_ref = cls._collection().document(rec.recommendation_id)
        existing = doc_ref.get()
        if existing.exists:
            existing_data = existing.to_dict()
            # If already approved/converted or dismissed, do not overwrite unless requested
            if existing_data.get("status") in (
                RecommendationStatus.APPROVED.value,
                RecommendationStatus.CONVERTED_TO_INTERVENTION.value,
                RecommendationStatus.DISMISSED.value,
            ):
                return InterventionRecommendation.from_firestore(existing.id, existing_data)

        doc_ref.set(rec.to_firestore())
        return rec

    @classmethod
    def get_student_recommendations(
        cls, student_id: str, status_filter: Optional[str] = None
    ) -> List[InterventionRecommendation]:
        query = cls._collection().where("student_id", "==", student_id)
        if status_filter:
            query = query.where("status", "==", status_filter)
        docs = query.stream()
        recs = [InterventionRecommendation.from_firestore(d.id, d.to_dict()) for d in docs]
        return cls._rank_recommendations(recs)

    @classmethod
    def get_pending_recommendations(
        cls, class_id: str
    ) -> List[InterventionRecommendation]:
        docs = (
            cls._collection()
            .where("class_id", "==", class_id)
            .where("status", "==", RecommendationStatus.PENDING.value)
            .stream()
        )
        recs = [InterventionRecommendation.from_firestore(d.id, d.to_dict()) for d in docs]
        return cls._rank_recommendations(recs)

    @classmethod
    def get_school_recommendations(
        cls, school_id: str, status_filter: Optional[str] = None
    ) -> List[InterventionRecommendation]:
        query = cls._collection().where("school_id", "==", school_id)
        if status_filter:
            query = query.where("status", "==", status_filter)
        docs = query.stream()
        recs = [InterventionRecommendation.from_firestore(d.id, d.to_dict()) for d in docs]
        return cls._rank_recommendations(recs)

    @classmethod
    def get_recommendation(
        cls, recommendation_id: str
    ) -> Optional[InterventionRecommendation]:
        doc = cls._collection().document(recommendation_id).get()
        if not doc.exists:
            return None
        return InterventionRecommendation.from_firestore(doc.id, doc.to_dict())

    # =========================================================================
    # Approval & Dismissal Workflows
    # =========================================================================

    @classmethod
    def approve_recommendation(
        cls,
        recommendation_id: str,
        user: CurrentUser,
        optional_type: Optional[InterventionType] = None,
        optional_notes: Optional[str] = None,
        optional_follow_up_date: Optional[str] = None,
    ) -> Tuple[InterventionRecommendation, Intervention]:
        """
        Approve recommendation -> Creates an actual Intervention via InterventionService
        Updates recommendation status to CONVERTED_TO_INTERVENTION and links intervention_id.
        """
        rec = cls.get_recommendation(recommendation_id)
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found.")

        require_school_access(rec.school_id, user)

        # 1. Create real Intervention
        now = datetime.now(tz=timezone.utc)
        follow_up = optional_follow_up_date or (
            (now + timedelta(days=rec.suggested_follow_up_days)).strftime("%Y-%m-%d")
        )
        chosen_type = optional_type or rec.recommendation_type
        notes = optional_notes or f"Approved Recommendation: {rec.explanation}"

        create_payload = InterventionCreate(
            school_id=rec.school_id,
            student_id=rec.student_id,
            class_id=rec.class_id,
            type=chosen_type,
            notes=notes,
            follow_up_date=follow_up,
        )

        intervention = InterventionService.create_intervention(
            data=create_payload,
            teacher_id=user.uid,
        )

        # 2. Update Recommendation
        doc_ref = cls._collection().document(recommendation_id)
        updates = {
            "status": RecommendationStatus.CONVERTED_TO_INTERVENTION.value,
            "intervention_id": intervention.id,
            "reviewed_by": user.uid,
            "reviewed_at": now,
            "updated_at": now,
        }
        doc_ref.update(updates)

        updated_rec = cls.get_recommendation(recommendation_id)
        return updated_rec, intervention

    @classmethod
    def dismiss_recommendation(
        cls,
        recommendation_id: str,
        user: CurrentUser,
        reason: str = DismissalReason.TEACHER_JUDGMENT.value,
        notes: Optional[str] = None,
    ) -> InterventionRecommendation:
        """
        Dismiss recommendation with reason and educator attribution.
        """
        rec = cls.get_recommendation(recommendation_id)
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found.")

        require_school_access(rec.school_id, user)

        now = datetime.now(tz=timezone.utc)
        doc_ref = cls._collection().document(recommendation_id)
        updates = {
            "status": RecommendationStatus.DISMISSED.value,
            "dismissal_reason": reason,
            "dismissal_notes": notes,
            "reviewed_by": user.uid,
            "reviewed_at": now,
            "updated_at": now,
        }
        doc_ref.update(updates)

        return cls.get_recommendation(recommendation_id)
