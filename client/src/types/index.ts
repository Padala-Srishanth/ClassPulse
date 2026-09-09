export type UserRole = 'ADMIN' | 'SCHOOL_ADMIN' | 'TEACHER' | 'STUDENT';

export interface User {
  id: string;
  firebase_uid: string;
  email: string;
  name: string;
  role: UserRole;
  school_id: string | null;
  status: string;
  student_id?: string; // Only set for STUDENT role
}

export interface School {
  id: string;
  name: string;
  code: string;
  district?: string;
  state?: string;
  country: string;
  status: string;
}

export interface SchoolClass {
  id: string;
  school_id: string;
  name: string;
  grade: string;
  section: string;
  academic_year: string;
  teacher_ids: string[];
  status: string;
}

export interface Student {
  id: string;
  school_id: string;
  class_id: string;
  student_code: string;
  name: string;
  grade: string;
  section: string;
  parent_contact?: string;
  status: string;
}


export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'INSUFFICIENT_DATA';

export interface SignalReason {
  signal_type: string;
  metric: string;
  baseline_value: number;
  current_value: number;
  change: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  explanation: string;
}

export interface WeeklyEngagementSignature {
  week_key: string;
  attendance_rate: number | null;
  attendance_present_count: number;
  attendance_total_count: number;
  homework_completion_rate: number | null;
  homework_completed_count: number;
  homework_total_count: number;
  average_test_percentage: number | null;
  test_count: number;
}

export interface RiskAlert {
  id: string;
  school_id: string;
  class_id: string;
  student_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  model_version: string;
  reasons: SignalReason[];
  signals: Record<string, any>;
  analysis_period: string;
  status: 'ACTIVE' | 'RESOLVED' | 'DISMISSED';
  created_at: string;
}

export interface StudentRiskAnalysis {
  student_id: string;
  school_id: string;
  class_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  model_version: string;
  analysis_period: string;
  reasons: SignalReason[];
  weekly_signatures: WeeklyEngagementSignature[];
  baseline: {
    has_sufficient_history: boolean;
    baseline_attendance_rate: number | null;
    baseline_homework_completion_rate: number | null;
    baseline_test_average: number | null;
  };
  trends: {
    recent_attendance_rate: number | null;
    recent_homework_completion_rate: number | null;
    recent_test_average: number | null;
    attendance_delta: number | null;
    homework_delta: number | null;
    test_delta: number | null;
    consecutive_dropping_weeks: number;
    multi_signal_decline_count: number;
  };
  alert?: RiskAlert;
}

export interface ClassRiskSummary {
  class_id: string;
  school_id: string;
  total_students: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  insufficient_data_count: number;
  alerts: RiskAlert[];
}


export type InterventionType =
  | 'ACADEMIC_SUPPORT'
  | 'PARENT_CONTACT'
  | 'COUNSELING_REFERRAL'
  | 'EXTRA_ASSIGNMENT'
  | 'ONE_ON_ONE_SUPPORT'
  | 'OTHER';

export type InterventionStatus =
  | 'PLANNED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED';

export type InterventionOutcome =
  | 'STUDENT_IMPROVED'
  | 'STUDENT_UNCHANGED'
  | 'STUDENT_DECLINED_FURTHER'
  | 'REFERRED_FOR_ADDITIONAL_SUPPORT'
  | 'OTHER';

export interface Intervention {
  id: string;
  school_id: string;
  student_id: string;
  teacher_id: string;
  class_id: string;
  type: InterventionType;
  notes: string;
  follow_up_date?: string;
  status: InterventionStatus;
  outcome?: InterventionOutcome;
  outcome_notes?: string;
  created_at: string;
  updated_at: string;
}

export type DataStatus = 'SUFFICIENT_DATA' | 'PARTIAL_DATA' | 'INSUFFICIENT_DATA' | 'NO_DATA';
export type TrendDirection = 'IMPROVING' | 'STABLE' | 'DECLINING' | 'INSUFFICIENT_HISTORY';

export interface MonthlyStudentReport {
  id: string;
  school_id: string;
  class_id: string;
  student_id: string;
  student_name: string;
  student_code?: string;
  report_period: string; // YYYY-MM
  year: number;
  month: number;
  generated_at: string;
  data_status: DataStatus;
  attendance: {
    total_school_days: number;
    days_present: number;
    days_absent: number;
    days_late: number;
    days_excused: number;
    attendance_percentage: number | null;
  };
  homework: {
    total_assignments: number;
    completed: number;
    not_completed: number;
    late: number;
    completion_rate: number | null;
  };
  academic: {
    total_tests: number;
    average_percentage: number | null;
    subject_breakdown: Record<string, {
      tests_count: number;
      average_percentage: number;
      highest_percentage: number;
      lowest_percentage: number;
    }>;
  };
  risk: {
    risk_score: number | null;
    risk_level: string;
    subscores: {
      attendance_drop: number;
      homework_drop: number;
      academic_drop: number;
    };
    multipliers: {
      persistence: number;
      cross_signal: number;
    };
    baseline_used: {
      has_sufficient_history: boolean;
      months_observed: number;
      baseline_attendance: number | null;
      baseline_homework: number | null;
      baseline_academic: number | null;
    };
    risk_factors: string[];
    positive_highlights: string[];
    recommended_interventions: string[];
  };
  trends: {
    previous_period: string | null;
    attendance_delta: number | null;
    attendance_direction: TrendDirection;
    homework_delta: number | null;
    homework_direction: TrendDirection;
    academic_delta: number | null;
    academic_direction: TrendDirection;
    risk_delta: number | null;
    risk_direction: TrendDirection;
    overall_direction: TrendDirection;
    consecutive_declining_months: number;
  };
}

export interface MonthlyClassReport {
  id: string;
  school_id: string;
  class_id: string;
  class_name: string;
  grade: string;
  section: string;
  report_period: string;
  year: number;
  month: number;
  generated_at: string;
  data_status: DataStatus;
  total_students: number;
  total_students_with_data: number;
  average_attendance: number | null;
  average_academic_percentage: number | null;
  subject_wise_average: Record<string, number>;
  average_homework_completion: number | null;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  needs_data_count: number;
  trends: {
    previous_period: string | null;
    attendance_delta: number | null;
    attendance_direction: TrendDirection;
    academic_delta: number | null;
    academic_direction: TrendDirection;
    homework_delta: number | null;
    homework_direction: TrendDirection;
  };
}

export interface MonthlySchoolReport {
  id: string;
  school_id: string;
  school_name: string;
  report_period: string;
  year: number;
  month: number;
  generated_at: string;
  data_status: DataStatus;
  total_students: number;
  total_classes: number;
  average_attendance: number | null;
  average_academic_percentage: number | null;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  needs_data_count: number;
  class_comparisons: Array<{
    class_id: string;
    class_name: string;
    grade: string;
    section: string;
    total_students: number;
    average_attendance: number | null;
    average_academic_percentage: number | null;
    average_homework_completion: number | null;
    high_risk_count: number;
    medium_risk_count: number;
    low_risk_count: number;
  }>;
  student_risk_leaderboard: Array<{
    student_id: string;
    student_name: string;
    student_code: string;
    class_id: string;
    risk_score: number;
    risk_level: string;
    primary_risk_factor: string;
    attendance_percentage: number | null;
    academic_percentage: number | null;
  }>;
  monthly_interventions: {
    total_logged: number;
    active_count: number;
    completed_count: number;
  };
  trends: {
    previous_period: string | null;
    attendance_delta: number | null;
    attendance_direction: TrendDirection;
    academic_delta: number | null;
    academic_direction: TrendDirection;
  };
}
