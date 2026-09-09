import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Award,
  BookOpen,
  Calendar,
  CheckCircle2,
  ChevronRight,
  GraduationCap,
  RefreshCw,
  School as SchoolIcon,
  TrendingDown,
  TrendingUp,
  UserCheck,
  Users,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  getReportingPeriods,
  getSchoolMonthlyReport,
  generateSchoolMonthlyReport,
} from '../../api/monthly_reports';
import { MonthlyPeriodSelector } from '../../components/monthly/MonthlyPeriodSelector';
import { MonthlyRiskBadge } from '../../components/monthly/MonthlyRiskBadge';
import { MonthlyTrendBadge } from '../../components/monthly/MonthlyTrendBadge';
import { useAuth } from '../../context/AuthContext';
import { MonthlySchoolReport } from '../../types';

export const PrincipalMonthlyAnalyticsPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [periods, setPeriods] = useState<string[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('2026-09');
  const [schoolReport, setSchoolReport] = useState<MonthlySchoolReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const schoolId = currentUser?.school_id || 'school-001';

  useEffect(() => {
    async function loadPeriods() {
      try {
        const pList = await getReportingPeriods();
        setPeriods(pList);
        if (pList.length > 0) {
          setSelectedPeriod(pList[pList.length - 1]);
        }
      } catch (err) {
        console.error('Failed to load periods', err);
      }
    }
    loadPeriods();
  }, []);

  const loadSchoolData = async (force = false) => {
    if (!selectedPeriod) return;
    try {
      setLoading(true);
      let rep: MonthlySchoolReport;
      if (force) {
        rep = await generateSchoolMonthlyReport(schoolId, selectedPeriod);
      } else {
        rep = await getSchoolMonthlyReport(schoolId, selectedPeriod);
      }
      setSchoolReport(rep);
    } catch (err) {
      console.error('Failed to load school monthly report', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadSchoolData();
  }, [selectedPeriod]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadSchoolData(true);
  };

  const chartData = (schoolReport?.class_comparisons || []).map((c) => ({
    name: c.class_name.replace('Grade ', ''),
    attendance: c.average_attendance || 0,
    academic: c.average_academic_percentage || 0,
    highRisk: c.high_risk_count || 0,
  }));

  return (
    <div className="monthly-container">
      {/* Hero Header */}
      <div className="monthly-hero">
        <div className="monthly-hero-header">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span className="monthly-tag">Executive School Intelligence</span>
            <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
              School-Wide Monthly Analytics & Longitudinal Risk Intelligence
            </h1>
            <p style={{ fontSize: '0.85rem', color: '#cbd5e1', maxWidth: '650px' }}>
              Executive benchmark of {schoolReport?.school_name || 'Delhi Public School'}, tracking cross-cohort performance and early warning triggers.
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
              title="Regenerate School Report"
            >
              <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      {loading && !schoolReport ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '240px', gap: '12px', color: '#64748b' }}>
          <RefreshCw size={32} color="#4f46e5" className="animate-spin" />
          <p style={{ fontSize: '0.9rem' }}>Aggregating school-wide monthly intelligence...</p>
        </div>
      ) : schoolReport ? (
        <>
          {/* Top KPI Cards */}
          <div className="monthly-stat-grid">
            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">Total Students</span>
                <div className="monthly-stat-icon" style={{ background: '#e0e7ff', color: '#4f46e5' }}>
                  <GraduationCap size={20} />
                </div>
              </div>
              <div className="monthly-stat-val">{schoolReport.total_students}</div>
              <div className="monthly-stat-footer">
                <span>Across {schoolReport.total_classes} Classes</span>
              </div>
            </div>

            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">School Attendance Avg</span>
                <div className="monthly-stat-icon" style={{ background: '#e0f2fe', color: '#0284c7' }}>
                  <UserCheck size={20} />
                </div>
              </div>
              <div className="monthly-stat-val">
                {schoolReport.average_attendance !== null ? `${schoolReport.average_attendance.toFixed(1)}%` : 'N/A'}
              </div>
              <div className="monthly-stat-footer">
                <span>Month-over-Month</span>
                <MonthlyTrendBadge
                  delta={schoolReport.trends?.attendance_delta}
                  direction={schoolReport.trends?.attendance_direction}
                />
              </div>
            </div>

            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">School Academic Avg</span>
                <div className="monthly-stat-icon" style={{ background: '#dcfce7', color: '#16a34a' }}>
                  <Award size={20} />
                </div>
              </div>
              <div className="monthly-stat-val">
                {schoolReport.average_academic_percentage !== null
                  ? `${schoolReport.average_academic_percentage.toFixed(1)}%`
                  : 'N/A'}
              </div>
              <div className="monthly-stat-footer">
                <span>Month-over-Month</span>
                <MonthlyTrendBadge
                  delta={schoolReport.trends?.academic_delta}
                  direction={schoolReport.trends?.academic_direction}
                />
              </div>
            </div>

            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">Total High Risk</span>
                <div className="monthly-stat-icon" style={{ background: '#ffe4e6', color: '#e11d48' }}>
                  <AlertTriangle size={20} />
                </div>
              </div>
              <div className="monthly-stat-val" style={{ color: '#e11d48' }}>
                {schoolReport.high_risk_count}
              </div>
              <div className="monthly-stat-footer">
                <span>{schoolReport.medium_risk_count} Med • {schoolReport.low_risk_count} Low</span>
              </div>
            </div>
          </div>

          {/* Class Comparisons Chart */}
          <div className="monthly-chart-card">
            <div className="monthly-chart-header">
              <div>
                <h3 className="monthly-chart-title">Class-by-Class Comparative Performance</h3>
                <p className="monthly-chart-subtitle">Comparing attendance and academic marks averages across all classes</p>
              </div>
            </div>

            <div style={{ width: '100%', height: '320px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.8} />
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#475569', fontSize: 11 }} />
                  <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fill: '#475569', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderColor: '#e2e8f0',
                      borderRadius: '12px',
                      color: '#0f172a',
                      fontSize: '12px',
                      boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '12px', fontSize: '12px' }} />
                  <Bar dataKey="attendance" name="Attendance %" fill="#0284c7" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="academic" name="Academic %" fill="#16a34a" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Leaderboard: Top At-Risk Students Across School */}
          <div className="monthly-table-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={18} color="#e11d48" />
                  Urgent Intervention Priority Leaderboard (Top At-Risk Students)
                </h3>
                <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
                  School-wide rank by drop magnitude and persistence triggers for administrative intervention
                </p>
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table className="monthly-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Student</th>
                    <th>Class</th>
                    <th>Risk Score</th>
                    <th>Primary Trigger</th>
                    <th>Attendance</th>
                    <th>Academic</th>
                  </tr>
                </thead>
                <tbody>
                  {schoolReport.student_risk_leaderboard.map((item, idx) => (
                    <tr key={item.student_id}>
                      <td style={{ fontWeight: 800, color: '#64748b' }}>#{idx + 1}</td>
                      <td>
                        <div style={{ fontWeight: 700, color: '#0f172a' }}>{item.student_name}</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace' }}>{item.student_code}</div>
                      </td>
                      <td style={{ fontWeight: 600, color: '#334155' }}>
                        {item.class_id.replace('class-', '').toUpperCase()}
                      </td>
                      <td>
                        <MonthlyRiskBadge level={item.risk_level} score={item.risk_score} size="sm" />
                      </td>
                      <td style={{ fontSize: '0.8rem', color: '#334155', maxWidth: '280px' }}>
                        {item.primary_risk_factor}
                      </td>
                      <td style={{ fontSize: '0.8rem', fontWeight: 700, color: '#0f172a' }}>
                        {item.attendance_percentage ? `${item.attendance_percentage.toFixed(1)}%` : 'N/A'}
                      </td>
                      <td style={{ fontSize: '0.8rem', fontWeight: 700, color: '#0f172a' }}>
                        {item.academic_percentage ? `${item.academic_percentage.toFixed(1)}%` : 'N/A'}
                      </td>
                    </tr>
                  ))}
                  {schoolReport.student_risk_leaderboard.length === 0 && (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
                        No students currently flagged in high-risk categories.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
