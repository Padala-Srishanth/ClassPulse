import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Calendar,
  Clock,
  GraduationCap,
  History,
  Layers,
  LineChart,
  RefreshCw,
  Sparkles,
  User,
} from 'lucide-react';
import { RiskBadge } from '../components/RiskBadge';
import { ReasonList } from '../components/ReasonList';
import { TrendCharts } from '../components/TrendCharts';
import { InterventionTimeline } from '../components/InterventionTimeline';
import { studentsApi } from '../api/students';
import { riskApi } from '../api/risk';
import { interventionsApi } from '../api/interventions';
import { Intervention, RiskAlert, Student, StudentRiskAnalysis } from '../types';

interface StudentDetailPageProps {
  studentId: string;
  onBack: () => void;
  onOpenIntervention: (student: Student) => void;
}

export const StudentDetailPage: React.FC<StudentDetailPageProps> = ({
  studentId,
  onBack,
  onOpenIntervention,
}) => {
  const [student, setStudent] = useState<Student | null>(null);
  const [analysis, setAnalysis] = useState<StudentRiskAnalysis | null>(null);
  const [historyAlerts, setHistoryAlerts] = useState<RiskAlert[]>([]);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [reanalyzing, setReanalyzing] = useState(false);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [stu, ana, hist, ints] = await Promise.all([
        studentsApi.getStudent(studentId),
        riskApi.analyzeStudent(studentId),
        riskApi.getStudentRiskHistory(studentId),
        interventionsApi.listStudentInterventions(studentId),
      ]);
      setStudent(stu);
      setAnalysis(ana);
      setHistoryAlerts(hist);
      setInterventions(ints);
    } catch (err) {
      console.error('Error loading student profile:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [studentId]);

  const handleReanalyze = async () => {
    setReanalyzing(true);
    try {
      const ana = await riskApi.analyzeStudent(studentId);
      setAnalysis(ana);
      const hist = await riskApi.getStudentRiskHistory(studentId);
      setHistoryAlerts(hist);
    } catch (e: any) {
      alert(e.message || 'Error re-running risk analysis');
    } finally {
      setReanalyzing(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}>
        Analyzing student historical baseline and trajectory...
      </div>
    );
  }

  if (!student || !analysis) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h3>Student profile not found</h3>
        <button className="btn btn-outline" onClick={onBack} style={{ marginTop: '16px' }}>
          <ArrowLeft size={16} /> Back to Directory
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <button className="btn btn-outline btn-sm" onClick={onBack}>
          <ArrowLeft size={16} />
          Back to Students
        </button>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-outline btn-sm" onClick={handleReanalyze} disabled={reanalyzing}>
            <RefreshCw size={14} className={reanalyzing ? 'spin' : ''} />
            {reanalyzing ? 'Recalculating...' : 'Refresh AI Analysis'}
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => onOpenIntervention(student)}>
            <GraduationCap size={16} />
            Create Intervention Plan
          </button>
        </div>
      </div>

      {/* Student Profile Card & Risk Score Banner */}
      <div
        className="card"
        style={{
          background: analysis.risk_level === 'HIGH' ? '#fff5f5' : (analysis.risk_level === 'MEDIUM' ? '#fffdf5' : '#ffffff'),
          borderColor: analysis.risk_level === 'HIGH' ? '#fecdd3' : (analysis.risk_level === 'MEDIUM' ? '#fde68a' : '#e2e8f0'),
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '16px',
              background: '#eef2ff',
              color: '#4f46e5',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '1.4rem',
            }}
          >
            {student.name.charAt(0)}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 700 }}>{student.name}</h2>
              <RiskBadge level={analysis.risk_level} score={analysis.risk_score} />
            </div>
            <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: '4px' }}>
              Student ID: <strong>{student.student_code}</strong> • Class: <strong>{student.grade}-{student.section}</strong> • Analysis Period: <strong>{analysis.analysis_period}</strong>
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '24px', textAlign: 'right' }}>
          <div>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
              Risk Score
            </span>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: analysis.risk_level === 'HIGH' ? '#e11d48' : (analysis.risk_level === 'MEDIUM' ? '#d97706' : '#16a34a') }}>
              {analysis.risk_score} <span style={{ fontSize: '1rem', color: '#94a3b8' }}>/ 100</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Explainability & Baseline Comparison */}
      <div className="grid-cols-2">
        {/* Left: Why this student was flagged */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Sparkles size={20} color="#4f46e5" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Why was this student flagged?</h3>
          </div>
          <p style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '16px' }}>
            Factual indicators computed by comparing the student's recent performance against their historical baseline.
          </p>
          <ReasonList reasons={analysis.reasons} />
        </div>

        {/* Right: Baseline vs Current Metrics */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Layers size={20} color="#0891b2" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Historical Baseline vs. Recent Window</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '12px' }}>
            <div style={{ padding: '12px 16px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Attendance Rate</span>
                <span style={{ fontSize: '0.82rem', color: (analysis.trends.attendance_delta || 0) < 0 ? '#e11d48' : '#15803d', fontWeight: 700 }}>
                  {analysis.trends.attendance_delta ? `${analysis.trends.attendance_delta > 0 ? '+' : ''}${analysis.trends.attendance_delta}%` : 'Stable'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: '#64748b' }}>
                <span>Baseline: {analysis.baseline.baseline_attendance_rate ? `${analysis.baseline.baseline_attendance_rate.toFixed(1)}%` : 'N/A'}</span>
                <span>Recent: {analysis.trends.recent_attendance_rate ? `${analysis.trends.recent_attendance_rate.toFixed(1)}%` : 'N/A'}</span>
              </div>
            </div>

            <div style={{ padding: '12px 16px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Homework Completion</span>
                <span style={{ fontSize: '0.82rem', color: (analysis.trends.homework_delta || 0) < 0 ? '#e11d48' : '#15803d', fontWeight: 700 }}>
                  {analysis.trends.homework_delta ? `${analysis.trends.homework_delta > 0 ? '+' : ''}${analysis.trends.homework_delta}%` : 'Stable'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: '#64748b' }}>
                <span>Baseline: {analysis.baseline.baseline_homework_completion_rate ? `${analysis.baseline.baseline_homework_completion_rate.toFixed(1)}%` : 'N/A'}</span>
                <span>Recent: {analysis.trends.recent_homework_completion_rate ? `${analysis.trends.recent_homework_completion_rate.toFixed(1)}%` : 'N/A'}</span>
              </div>
            </div>

            <div style={{ padding: '12px 16px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Test Score Average</span>
                <span style={{ fontSize: '0.82rem', color: (analysis.trends.test_delta || 0) < 0 ? '#e11d48' : '#15803d', fontWeight: 700 }}>
                  {analysis.trends.test_delta ? `${analysis.trends.test_delta > 0 ? '+' : ''}${analysis.trends.test_delta}%` : 'Stable'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: '#64748b' }}>
                <span>Baseline: {analysis.baseline.baseline_test_average ? `${analysis.baseline.baseline_test_average.toFixed(1)}%` : 'N/A'}</span>
                <span>Recent: {analysis.trends.recent_test_average ? `${analysis.trends.recent_test_average.toFixed(1)}%` : 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Academic Trend Charts */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <LineChart size={20} color="#4f46e5" />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Longitudinal Academic Trajectories</h3>
        </div>
        <TrendCharts
          signatures={analysis.weekly_signatures}
          baselineAttendance={analysis.baseline.baseline_attendance_rate}
          baselineHomework={analysis.baseline.baseline_homework_completion_rate}
          baselineTest={analysis.baseline.baseline_test_average}
        />
      </div>

      {/* Interventions Section */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Intervention History & Action Plans</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Track remedial actions taken by teachers and recorded follow-up outcomes.
            </p>
          </div>
          <button className="btn btn-primary btn-sm" onClick={() => onOpenIntervention(student)}>
            <GraduationCap size={16} /> Record Action Plan
          </button>
        </div>

        <InterventionTimeline
          interventions={interventions}
          onRefresh={loadAllData}
        />
      </div>
    </div>
  );
};
