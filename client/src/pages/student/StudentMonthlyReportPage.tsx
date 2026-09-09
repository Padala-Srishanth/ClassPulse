import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Award,
  BookOpen,
  Calendar,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  UserCheck,
} from 'lucide-react';
import {
  getReportingPeriods,
  getStudentMonthlyHistory,
  getStudentMonthlyReport,
  generateStudentMonthlyReport,
} from '../../api/monthly_reports';
import { MonthlyPeriodSelector } from '../../components/monthly/MonthlyPeriodSelector';
import { MonthlyRiskBadge } from '../../components/monthly/MonthlyRiskBadge';
import { MonthlyTrendBadge } from '../../components/monthly/MonthlyTrendBadge';
import { RiskTrajectoryChart } from '../../components/monthly/RiskTrajectoryChart';
import { SubjectPerformanceChart } from '../../components/monthly/SubjectPerformanceChart';
import { MonthlyStudentReport } from '../../types';

export const StudentMonthlyReportPage: React.FC = () => {
  const [periods, setPeriods] = useState<string[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('2026-09');
  const [report, setReport] = useState<MonthlyStudentReport | null>(null);
  const [history, setHistory] = useState<MonthlyStudentReport[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const getStudentId = () => {
    try {
      const saved = localStorage.getItem('classpulse_demo_user');
      if (saved) {
        const u = JSON.parse(saved);
        if (u.student_id) return u.student_id;
        if (u.role === 'STUDENT' && u.uid) return u.uid;
      }
    } catch (e) {
      // ignore
    }
    return 'demo-student-001';
  };

  const studentId = getStudentId();

  useEffect(() => {
    async function loadPeriods() {
      try {
        const pList = await getReportingPeriods();
        setPeriods(pList);
        if (pList.length > 0 && !pList.includes(selectedPeriod)) {
          setSelectedPeriod(pList[pList.length - 1]);
        }
      } catch (err) {
        setPeriods(['2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09']);
      }
    }
    loadPeriods();
  }, []);

  const loadReportData = async (period: string, force = false) => {
    try {
      setLoading(true);
      setError(null);
      let rep: MonthlyStudentReport;
      if (force) {
        rep = await generateStudentMonthlyReport(studentId, period);
      } else {
        rep = await getStudentMonthlyReport(studentId, period);
      }
      setReport(rep);

      const hist = await getStudentMonthlyHistory(studentId);
      setHistory(hist);
    } catch (err: any) {
      setError(err.message || 'Failed to load monthly report.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (selectedPeriod) {
      loadReportData(selectedPeriod);
    }
  }, [selectedPeriod]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadReportData(selectedPeriod, true);
  };

  return (
    <div className="monthly-container">
      {/* Hero Header */}
      <div className="monthly-hero">
        <div className="monthly-hero-header">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className="monthly-tag">Student Monthly Dossier</span>
              {report && (
                <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                  ID: {report.student_code || report.student_id}
                </span>
              )}
            </div>
            <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
              {report?.student_name ? `${report.student_name}'s Monthly Academic Report` : 'Student Monthly Report'}
            </h1>
            <p style={{ fontSize: '0.85rem', color: '#cbd5e1', maxWidth: '650px' }}>
              Transparent monthly summary tracking your attendance consistency, assignment completion, test score trajectory, and personalized improvement guidance.
            </p>
          </div>

          <div className="monthly-hero-controls">
            <MonthlyPeriodSelector
              periods={periods}
              selectedPeriod={selectedPeriod}
              onChange={setSelectedPeriod}
              isLoading={loading || refreshing}
            />
            <button
              onClick={handleRefresh}
              disabled={refreshing || loading}
              className="monthly-btn-icon"
              title="Regenerate Report"
            >
              <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {report && (
          <div className="monthly-hero-footer">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em', color: '#94a3b8' }}>
                Overall Assessment:
              </span>
              <MonthlyRiskBadge
                level={report.risk?.risk_level}
                score={report.risk?.risk_score}
                size="md"
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.8rem', color: '#94a3b8' }}>
              <span>Data Status: <strong style={{ color: '#ffffff' }}>{report.data_status}</strong></span>
              <span>•</span>
              <span>Baseline: <strong style={{ color: '#ffffff' }}>{report.risk?.baseline_used?.months_observed || 0} months observed</strong></span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', borderRadius: '12px', padding: '16px', color: '#be123c', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertTriangle size={18} color="#e11d48" />
          <span>{error}</span>
        </div>
      )}

      {loading && !report ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '240px', gap: '12px', color: '#64748b' }}>
          <RefreshCw size={32} color="#4f46e5" className="animate-spin" />
          <p style={{ fontSize: '0.9rem' }}>Loading longitudinal student report...</p>
        </div>
      ) : report ? (
        <>
          {/* Stat Cards Grid */}
          <div className="monthly-stat-grid">
            {/* Attendance */}
            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">Monthly Attendance</span>
                <div className="monthly-stat-icon" style={{ background: '#e0f2fe', color: '#0284c7' }}>
                  <UserCheck size={20} />
                </div>
              </div>
              <div className="monthly-stat-val">
                {report.attendance.attendance_percentage !== null
                  ? `${report.attendance.attendance_percentage.toFixed(1)}%`
                  : 'No Data'}
              </div>
              <div className="monthly-stat-footer">
                <span>
                  {report.attendance.days_present}P / {report.attendance.days_late}L / {report.attendance.days_absent}A
                </span>
                <MonthlyTrendBadge
                  delta={report.trends?.attendance_delta}
                  direction={report.trends?.attendance_direction}
                />
              </div>
            </div>

            {/* Homework */}
            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">Homework Completion</span>
                <div className="monthly-stat-icon" style={{ background: '#f3e8ff', color: '#7c3aed' }}>
                  <BookOpen size={20} />
                </div>
              </div>
              <div className="monthly-stat-val">
                {report.homework.completion_rate !== null
                  ? `${report.homework.completion_rate.toFixed(1)}%`
                  : 'No Data'}
              </div>
              <div className="monthly-stat-footer">
                <span>
                  {report.homework.completed} of {report.homework.total_assignments} Completed
                </span>
                <MonthlyTrendBadge
                  delta={report.trends?.homework_delta}
                  direction={report.trends?.homework_direction}
                />
              </div>
            </div>

            {/* Academic */}
            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">Academic Marks Avg</span>
                <div className="monthly-stat-icon" style={{ background: '#dcfce7', color: '#16a34a' }}>
                  <Award size={20} />
                </div>
              </div>
              <div className="monthly-stat-val">
                {report.academic.average_percentage !== null
                  ? `${report.academic.average_percentage.toFixed(1)}%`
                  : 'No Tests'}
              </div>
              <div className="monthly-stat-footer">
                <span>{report.academic.total_tests} Tests Logged</span>
                <MonthlyTrendBadge
                  delta={report.trends?.academic_delta}
                  direction={report.trends?.academic_direction}
                />
              </div>
            </div>

            {/* Risk Score */}
            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">Drop Risk Score</span>
                <div className="monthly-stat-icon" style={{ background: '#ffe4e6', color: '#e11d48' }}>
                  <AlertTriangle size={20} />
                </div>
              </div>
              <div className="monthly-stat-val" style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                {report.risk.risk_score !== null ? (
                  <>
                    <span>{report.risk.risk_score.toFixed(1)}</span>
                    <span style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 500 }}>/ 100</span>
                  </>
                ) : (
                  <span style={{ fontSize: '1.25rem', color: '#64748b' }}>N/A</span>
                )}
              </div>
              <div className="monthly-stat-footer">
                <span>
                  Drop: {report.risk.subscores ? `-${report.risk.subscores.attendance_drop.toFixed(0)}% att` : 'none'}
                </span>
                <MonthlyTrendBadge
                  delta={report.trends?.risk_delta}
                  direction={report.trends?.risk_direction}
                  inverse={true}
                />
              </div>
            </div>
          </div>

          {/* 6-Month Trajectory Chart */}
          <RiskTrajectoryChart history={history} />

          {/* Subject Breakdown Chart */}
          <SubjectPerformanceChart subjects={report.academic.subject_breakdown} />

          {/* 3-Column Explainability Grid */}
          <div className="monthly-explain-grid">
            {/* Risk Factors */}
            <div className="monthly-explain-card">
              <div className="monthly-explain-card-header">
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: '#ffe4e6', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#e11d48' }}>
                  <AlertTriangle size={18} />
                </div>
                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>Risk Triggers</h4>
                  <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Identified drops below baseline</p>
                </div>
              </div>
              {report.risk.risk_factors && report.risk.risk_factors.length > 0 ? (
                <ul className="monthly-explain-list">
                  {report.risk.risk_factors.map((f, i) => (
                    <li key={i} className="monthly-explain-item">
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#e11d48', marginTop: '6px', flexShrink: 0 }} />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic' }}>No risk drivers detected.</p>
              )}
            </div>

            {/* Positive Highlights */}
            <div className="monthly-explain-card">
              <div className="monthly-explain-card-header">
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: '#dcfce7', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#16a34a' }}>
                  <CheckCircle2 size={18} />
                </div>
                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>Positive Highlights</h4>
                  <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Healthy engagement signals</p>
                </div>
              </div>
              {report.risk.positive_highlights && report.risk.positive_highlights.length > 0 ? (
                <ul className="monthly-explain-list">
                  {report.risk.positive_highlights.map((h, i) => (
                    <li key={i} className="monthly-explain-item">
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#16a34a', marginTop: '6px', flexShrink: 0 }} />
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic' }}>No highlights logged.</p>
              )}
            </div>

            {/* Recommendations */}
            <div className="monthly-explain-card">
              <div className="monthly-explain-card-header">
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: '#e0e7ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4f46e5' }}>
                  <Sparkles size={18} />
                </div>
                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>Actionable Guidance</h4>
                  <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Recommended support steps</p>
                </div>
              </div>
              {report.risk.recommended_interventions && report.risk.recommended_interventions.length > 0 ? (
                <ul className="monthly-explain-list">
                  {report.risk.recommended_interventions.map((rec, i) => (
                    <li key={i} className="monthly-explain-item">
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#4f46e5', marginTop: '6px', flexShrink: 0 }} />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic' }}>Continue routine academic schedule.</p>
              )}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
