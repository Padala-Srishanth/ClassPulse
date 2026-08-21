export type UserRole = 'ADMIN' | 'SCHOOL_ADMIN' | 'TEACHER';

export interface User {
  id: string;
  firebase_uid: string;
  email: string;
  name: string;
  role: UserRole;
  school_id: string | null;
  status: string;
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
