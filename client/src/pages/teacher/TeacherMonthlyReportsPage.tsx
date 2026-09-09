import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Award,
  BookOpen,
  Calendar,
  CheckCircle2,
  ChevronRight,
  RefreshCw,
  Search,
  UserCheck,
  Users,
  X,
} from 'lucide-react';
import {
  getClassMonthlyReport,
  generateClassMonthlyReport,
  getReportingPeriods,
  getStudentMonthlyReport,
  getStudentMonthlyHistory,
} from '../../api/monthly_reports';
import { MonthlyPeriodSelector } from '../../components/monthly/MonthlyPeriodSelector';
import { MonthlyRiskBadge } from '../../components/monthly/MonthlyRiskBadge';
import { MonthlyTrendBadge } from '../../components/monthly/MonthlyTrendBadge';
import { RiskTrajectoryChart } from '../../components/monthly/RiskTrajectoryChart';
import { SubjectPerformanceChart } from '../../components/monthly/SubjectPerformanceChart';
import { useAuth } from '../../context/AuthContext';
import { classesApi } from '../../api/classes';
import { studentsApi } from '../../api/students';
import { MonthlyClassReport, MonthlyStudentReport, SchoolClass, Student } from '../../types';

export const TeacherMonthlyReportsPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<string>('class-10a');
  const [periods, setPeriods] = useState<string[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('2026-09');

  const [classReport, setClassReport] = useState<MonthlyClassReport | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [studentReports, setStudentReports] = useState<Record<string, MonthlyStudentReport>>({});

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [riskFilter, setRiskFilter] = useState<string>('ALL');

  // Detail Modal state
  const [activeStudent, setActiveStudent] = useState<Student | null>(null);
  const [activeStudentReport, setActiveStudentReport] = useState<MonthlyStudentReport | null>(null);
  const [activeStudentHistory, setActiveStudentHistory] = useState<MonthlyStudentReport[]>([]);
  const [modalLoading, setModalLoading] = useState<boolean>(false);

  useEffect(() => {
    async function loadInitial() {
      try {
        const [clsList, pList] = await Promise.all([
          classesApi.listSchoolClasses(currentUser?.school_id || 'school-001'),
          getReportingPeriods().catch(() => ['2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09']),
        ]);
        setClasses(clsList);
        if (clsList.length > 0 && !clsList.some((c) => c.id === selectedClassId)) {
          setSelectedClassId(clsList[0].id);
        }
        setPeriods(pList);
        if (pList.length > 0) {
          setSelectedPeriod(pList[pList.length - 1]);
        }
      } catch (err) {
        console.error('Initial load failed', err);
      }
    }
    loadInitial();
  }, [currentUser?.school_id]);

  const fetchCohortData = async (force = false) => {
    if (!selectedClassId || !selectedPeriod) return;
    try {
      setLoading(true);
      setError(null);
      let rep: MonthlyClassReport;
      if (force) {
        rep = await generateClassMonthlyReport(selectedClassId, selectedPeriod);
      } else {
        rep = await getClassMonthlyReport(selectedClassId, selectedPeriod);
      }
      setClassReport(rep);

      const stuList = await studentsApi.listClassStudents(selectedClassId);
      setStudents(stuList || []);

      const reps: Record<string, MonthlyStudentReport> = {};
      if (stuList && stuList.length > 0) {
        await Promise.all(
          stuList.map(async (s) => {
            try {
              const r = await getStudentMonthlyReport(s.id, selectedPeriod);
              reps[s.id] = r;
            } catch (e) {
              // ignore individual student fetch errors to avoid blocking the cohort
            }
          })
        );
      }
      setStudentReports(reps);
    } catch (err: any) {
      console.error('Failed to load class report', err);
      setError(err?.message || 'Failed to load class monthly report');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchCohortData();
  }, [selectedClassId, selectedPeriod]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchCohortData(true);
  };

  const handleOpenStudentDetail = async (student: Student) => {
    setActiveStudent(student);
    setModalLoading(true);
    try {
      const rep = await getStudentMonthlyReport(student.id, selectedPeriod);
      const hist = await getStudentMonthlyHistory(student.id);
      setActiveStudentReport(rep);
      setActiveStudentHistory(hist);
    } catch (e) {
      console.error('Failed to load student detail', e);
    } finally {
      setModalLoading(false);
    }
  };

  const filteredStudents = students.filter((s) => {
    const rep = studentReports[s.id];
    const matchesSearch =
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.student_code.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;
    if (riskFilter === 'ALL') return true;
    const rLevel = rep?.risk?.risk_level || 'NO_DATA';
    return rLevel === riskFilter;
  });

  return (
    <div className="monthly-container">
      {/* Hero Header */}
      <div className="monthly-hero">
        <div className="monthly-hero-header">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span className="monthly-tag">Class Cohort Reporting</span>
            <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
              Class Monthly Reports & Cohort Analytics
            </h1>
            <p style={{ fontSize: '0.85rem', color: '#cbd5e1', maxWidth: '650px' }}>
              Aggregated monthly academic, attendance, and homework benchmarks with student-level drop detection.
            </p>
          </div>

          <div className="monthly-hero-controls">
            {/* Class Dropdown */}
            <div className="monthly-selector-box">
              <Users size={18} color="#818cf8" />
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8' }}>
                  Select Class
                </span>
                <select
                  value={selectedClassId}
                  onChange={(e) => setSelectedClassId(e.target.value)}
                >
                  {classes.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.grade}-{c.section})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Period Selector */}
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
              title="Regenerate Class Report"
            >
              <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', borderRadius: '12px', padding: '16px', color: '#be123c', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertTriangle size={18} color="#e11d48" />
          <span>{error}</span>
        </div>
      )}

      {loading && !classReport ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '240px', gap: '12px', color: '#64748b' }}>
          <RefreshCw size={32} color="#4f46e5" className="animate-spin" />
          <p style={{ fontSize: '0.9rem' }}>Aggregating cohort monthly data...</p>
        </div>
      ) : classReport ? (
        <>
          {/* Cohort Overview Stat Cards */}
          <div className="monthly-stat-grid">
            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">Enrolled Students</span>
                <div className="monthly-stat-icon" style={{ background: '#e0e7ff', color: '#4f46e5' }}>
                  <Users size={20} />
                </div>
              </div>
              <div className="monthly-stat-val">{classReport.total_students}</div>
              <div className="monthly-stat-footer">
                <span>{classReport.total_students_with_data} with logged data ({classReport.data_status})</span>
              </div>
            </div>

            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">Class Attendance Avg</span>
                <div className="monthly-stat-icon" style={{ background: '#e0f2fe', color: '#0284c7' }}>
                  <UserCheck size={20} />
                </div>
              </div>
              <div className="monthly-stat-val">
                {classReport.average_attendance !== null ? `${classReport.average_attendance.toFixed(1)}%` : 'N/A'}
              </div>
              <div className="monthly-stat-footer">
                <span>Month-over-Month</span>
                <MonthlyTrendBadge
                  delta={classReport.trends?.attendance_delta}
                  direction={classReport.trends?.attendance_direction}
                />
              </div>
            </div>

            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">Academic Marks Avg</span>
                <div className="monthly-stat-icon" style={{ background: '#dcfce7', color: '#16a34a' }}>
                  <Award size={20} />
                </div>
              </div>
              <div className="monthly-stat-val">
                {classReport.average_academic_percentage !== null
                  ? `${classReport.average_academic_percentage.toFixed(1)}%`
                  : 'N/A'}
              </div>
              <div className="monthly-stat-footer">
                <span>Month-over-Month</span>
                <MonthlyTrendBadge
                  delta={classReport.trends?.academic_delta}
                  direction={classReport.trends?.academic_direction}
                />
              </div>
            </div>

            <div className="monthly-stat-card">
              <div className="monthly-stat-top">
                <span className="monthly-stat-label">Homework Completion</span>
                <div className="monthly-stat-icon" style={{ background: '#f3e8ff', color: '#7c3aed' }}>
                  <BookOpen size={20} />
                </div>
              </div>
              <div className="monthly-stat-val">
                {classReport.average_homework_completion !== null
                  ? `${classReport.average_homework_completion.toFixed(1)}%`
                  : 'N/A'}
              </div>
              <div className="monthly-stat-footer">
                <span>Month-over-Month</span>
                <MonthlyTrendBadge
                  delta={classReport.trends?.homework_delta}
                  direction={classReport.trends?.homework_direction}
                />
              </div>
            </div>
          </div>

          {/* Risk Breakdown Pills Bar */}
          <div className="monthly-pills-bar">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#0f172a' }}>Cohort Risk Profile:</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <button
                onClick={() => setRiskFilter('ALL')}
                className="monthly-pill-btn"
                style={{
                  background: riskFilter === 'ALL' ? '#4f46e5' : '#f1f5f9',
                  color: riskFilter === 'ALL' ? '#ffffff' : '#475569',
                }}
              >
                All Students ({students.length})
              </button>
              <button
                onClick={() => setRiskFilter('HIGH')}
                className="monthly-pill-btn"
                style={{
                  background: riskFilter === 'HIGH' ? '#e11d48' : '#fff1f2',
                  color: riskFilter === 'HIGH' ? '#ffffff' : '#be123c',
                  border: '1px solid #fecdd3',
                }}
              >
                High Risk ({classReport.high_risk_count})
              </button>
              <button
                onClick={() => setRiskFilter('MEDIUM')}
                className="monthly-pill-btn"
                style={{
                  background: riskFilter === 'MEDIUM' ? '#d97706' : '#fffbeb',
                  color: riskFilter === 'MEDIUM' ? '#ffffff' : '#b45309',
                  border: '1px solid #fde68a',
                }}
              >
                Medium Risk ({classReport.medium_risk_count})
              </button>
              <button
                onClick={() => setRiskFilter('LOW')}
                className="monthly-pill-btn"
                style={{
                  background: riskFilter === 'LOW' ? '#16a34a' : '#f0fdf4',
                  color: riskFilter === 'LOW' ? '#ffffff' : '#15803d',
                  border: '1px solid #bbf7d0',
                }}
              >
                Low Risk ({classReport.low_risk_count})
              </button>
              <button
                onClick={() => setRiskFilter('INSUFFICIENT_DATA')}
                className="monthly-pill-btn"
                style={{
                  background: riskFilter === 'INSUFFICIENT_DATA' ? '#475569' : '#f8fafc',
                  color: riskFilter === 'INSUFFICIENT_DATA' ? '#ffffff' : '#64748b',
                  border: '1px solid #cbd5e1',
                }}
              >
                Needs Data ({classReport.needs_data_count})
              </button>
            </div>
          </div>

          {/* Student Roster Table */}
          <div className="monthly-table-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0f172a' }}>Student Monthly Cohort Roster</h3>
                <p style={{ fontSize: '0.8rem', color: '#64748b' }}>Click any student row to inspect their complete 6-month trajectory and risk drivers</p>
              </div>

              <div style={{ position: 'relative', width: '280px' }}>
                <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '10px' }} />
                <input
                  type="text"
                  placeholder="Search student or code..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px 8px 36px',
                    borderRadius: '10px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.85rem',
                    outline: 'none',
                  }}
                />
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table className="monthly-table">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Attendance</th>
                    <th>Homework</th>
                    <th>Academic</th>
                    <th>Risk Evaluation</th>
                    <th style={{ textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.map((stu) => {
                    const r = studentReports[stu.id];
                    return (
                      <tr
                        key={stu.id}
                        onClick={() => handleOpenStudentDetail(stu)}
                        style={{ cursor: 'pointer' }}
                      >
                        <td>
                          <div style={{ fontWeight: 700, color: '#0f172a' }}>{stu.name}</div>
                          <div style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace' }}>{stu.student_code}</div>
                        </td>
                        <td>
                          {r?.attendance?.attendance_percentage !== null && r?.attendance?.attendance_percentage !== undefined ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ fontWeight: 600 }}>{r.attendance.attendance_percentage.toFixed(1)}%</span>
                              <MonthlyTrendBadge
                                delta={r.trends?.attendance_delta}
                                direction={r.trends?.attendance_direction}
                              />
                            </div>
                          ) : (
                            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>No data</span>
                          )}
                        </td>
                        <td>
                          {r?.homework?.completion_rate !== null && r?.homework?.completion_rate !== undefined ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ fontWeight: 600 }}>{r.homework.completion_rate.toFixed(1)}%</span>
                              <MonthlyTrendBadge
                                delta={r.trends?.homework_delta}
                                direction={r.trends?.homework_direction}
                              />
                            </div>
                          ) : (
                            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>No data</span>
                          )}
                        </td>
                        <td>
                          {r?.academic?.average_percentage !== null && r?.academic?.average_percentage !== undefined ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ fontWeight: 600 }}>{r.academic.average_percentage.toFixed(1)}%</span>
                              <MonthlyTrendBadge
                                delta={r.trends?.academic_delta}
                                direction={r.trends?.academic_direction}
                              />
                            </div>
                          ) : (
                            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>No tests</span>
                          )}
                        </td>
                        <td>
                          <MonthlyRiskBadge
                            level={r?.risk?.risk_level || 'NO_DATA'}
                            score={r?.risk?.risk_score}
                            size="sm"
                          />
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <button
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '6px 12px',
                              borderRadius: '8px',
                              background: '#e0e7ff',
                              color: '#4338ca',
                              border: 'none',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              cursor: 'pointer',
                            }}
                          >
                            <span>Dossier</span>
                            <ChevronRight size={14} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                  {filteredStudents.length === 0 && (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
                        No students matched the selected search or risk filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}

      {/* Student Detail Modal Drawer */}
      {activeStudent && (
        <div className="monthly-modal-overlay" onClick={() => setActiveStudent(null)}>
          <div className="monthly-modal-box" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>{activeStudent.name}</h3>
                <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
                  {activeStudent.student_code} • Grade {activeStudent.grade}-{activeStudent.section}
                </p>
              </div>
              <button
                onClick={() => setActiveStudent(null)}
                style={{ background: '#f1f5f9', border: 'none', borderRadius: '8px', padding: '8px', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={20} />
              </button>
            </div>

            {modalLoading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                <RefreshCw size={28} color="#4f46e5" className="animate-spin" style={{ margin: '0 auto 8px' }} />
                <p style={{ fontSize: '0.875rem' }}>Loading student history & dossier...</p>
              </div>
            ) : activeStudentReport ? (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', padding: '16px', borderRadius: '14px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: '#64748b' }}>Monthly Risk:</span>
                    <MonthlyRiskBadge
                      level={activeStudentReport.risk?.risk_level}
                      score={activeStudentReport.risk?.risk_score}
                      size="md"
                    />
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                    Period: <strong style={{ color: '#0f172a' }}>{selectedPeriod}</strong>
                  </div>
                </div>

                {/* Trajectory */}
                <RiskTrajectoryChart history={activeStudentHistory} />

                {/* Risk Triggers & Recommendations */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                  <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', borderRadius: '16px', padding: '18px' }}>
                    <h5 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#be123c', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                      <AlertTriangle size={16} /> Observed Risk Drivers
                    </h5>
                    <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {activeStudentReport.risk.risk_factors?.map((f, i) => (
                        <li key={i} style={{ fontSize: '0.8rem', color: '#881337', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#e11d48', marginTop: '6px', flexShrink: 0 }} />
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div style={{ background: '#e0e7ff', border: '1px solid #c7d2fe', borderRadius: '16px', padding: '18px' }}>
                    <h5 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#3730a3', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                      <CheckCircle2 size={16} /> Recommended Interventions
                    </h5>
                    <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {activeStudentReport.risk.recommended_interventions?.map((rec, i) => (
                        <li key={i} style={{ fontSize: '0.8rem', color: '#312e81', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#4f46e5', marginTop: '6px', flexShrink: 0 }} />
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
