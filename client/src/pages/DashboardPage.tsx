import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  GraduationCap,
  Sparkles,
  Users,
} from 'lucide-react';
import { RiskCard } from '../components/RiskCard';
import { RiskBadge } from '../components/RiskBadge';
import { useAuth } from '../context/AuthContext';
import { classesApi } from '../api/classes';
import { studentsApi } from '../api/students';
import { riskApi } from '../api/risk';
import { recommendationsApi } from '../api/recommendations';
import { RiskAlert, SchoolClass, Student } from '../types';
import { AnnouncementsWidget } from '../components/AnnouncementsWidget';

interface DashboardPageProps {
  onSelectStudent: (studentId: string) => void;
  onOpenIntervention: (student: Student) => void;
  onOpenAttendance?: (classId: string, className: string, students: Student[]) => void;
  onOpenCreateStudent?: () => void;
  onNavigate?: (page: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onSelectStudent,
  onOpenIntervention,
  onOpenAttendance,
  onOpenCreateStudent,
  onNavigate,
}) => {
  const { schoolId } = useAuth();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<string>('');
  const [students, setStudents] = useState<Student[]>([]);
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [classRecs, setClassRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  // Load classes on mount
  useEffect(() => {
    async function loadClasses() {
      const sid = schoolId || 'school-001';
      try {
        const clsList = await classesApi.listSchoolClasses(sid);
        setClasses(clsList);
        if (clsList.length > 0 && !selectedClassId) {
          setSelectedClassId(clsList[0].id);
        }
      } catch (err) {
        console.error('Error fetching classes:', err);
      } finally {
        setLoading(false);
      }
    }
    loadClasses();
  }, [schoolId]);

  useEffect(() => {
    if (classes.length > 0 && (!selectedClassId || !classes.some((c) => c.id === selectedClassId))) {
      setSelectedClassId(classes[0].id);
    }
  }, [classes, selectedClassId]);

  // Load class data & alerts
  useEffect(() => {
    async function loadClassData() {
      if (!selectedClassId) return;
      setLoading(true);
      try {
        const [stus, activeAlerts, recs] = await Promise.all([
          studentsApi.listClassStudents(selectedClassId),
          riskApi.getClassActiveAlerts(selectedClassId).catch(() => []),
          recommendationsApi.getClassRecommendations(selectedClassId).catch(() => []),
        ]);
        setStudents(stus || []);
        setAlerts(activeAlerts || []);
        setClassRecs(recs || []);
      } catch (err) {
        console.error('Error loading class students/alerts:', err);
      } finally {
        setLoading(false);
      }
    }
    loadClassData();
  }, [selectedClassId]);

  const handleRunClassAnalysis = async () => {
    if (!selectedClassId) return;
    setAnalyzing(true);
    try {
      const summary = await riskApi.analyzeClass(selectedClassId);
      setAlerts(summary.alerts);
    } catch (err: any) {
      alert(err.message || 'Error running class AI risk analysis');
    } finally {
      setAnalyzing(false);
    }
  };

  const [showAllCohort, setShowAllCohort] = useState(false);

  const selectedClassObj = classes.find((c) => c.id === selectedClassId);
  const selectedClassName = selectedClassObj ? selectedClassObj.name : 'Class';

  const highRiskAlerts = alerts.filter((a) => a.risk_level === 'HIGH');
  const medRiskAlerts = alerts.filter((a) => a.risk_level === 'MEDIUM');
  const lowRiskAlerts = alerts.filter((a) => a.risk_level === 'LOW' || a.risk_level === 'INSUFFICIENT_DATA');
  const lowRiskCount = lowRiskAlerts.length + Math.max(0, students.length - alerts.length);

  const attentionAlerts = alerts.filter((a) => a.risk_level === 'HIGH' || a.risk_level === 'MEDIUM');
  const displayedAlerts = showAllCohort ? alerts : attentionAlerts;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top Welcome Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Teacher Early Warning Hub</h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Identify students exhibiting early indicators of learning decline before formal exams.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          {classes.length > 0 && (
            <select
              className="form-select"
              style={{ width: 'auto', fontWeight: 600 }}
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
            >
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.grade}-{c.section})
                </option>
              ))}
            </select>
          )}

          {onOpenAttendance && (
            <button
              className="btn btn-outline"
              onClick={() => onOpenAttendance(selectedClassId, selectedClassName, students)}
              disabled={students.length === 0}
            >
              Take Attendance
            </button>
          )}

          {onOpenCreateStudent && (
            <button className="btn btn-outline" onClick={onOpenCreateStudent}>
              + Add Student
            </button>
          )}

          <button
            className="btn btn-primary"
            onClick={handleRunClassAnalysis}
            disabled={analyzing || !selectedClassId}
          >
            <Sparkles size={16} />
            {analyzing ? 'Analyzing...' : 'Run AI Detection'}
          </button>
        </div>
      </div>

      {/* Principal Announcements Section */}
      <AnnouncementsWidget
        compact={true}
        maxItems={2}
        onViewAll={onNavigate ? () => onNavigate('teacher-announcements') : undefined}
      />

      {/* Recommended Actions Widget */}
      {(() => {
        const pendingRecs = classRecs.filter((r) => r.status === 'PENDING');
        const urgentCount = pendingRecs.filter((r) => r.priority_level === 'URGENT').length;
        const highCount = pendingRecs.filter((r) => r.priority_level === 'HIGH').length;

        if (pendingRecs.length === 0) return null;

        return (
          <div
            style={{
              background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)',
              borderRadius: 14,
              padding: '20px 24px',
              color: '#fff',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 16,
              boxShadow: '0 4px 15px rgba(49, 46, 129, 0.15)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{ background: 'rgba(255,255,255,0.15)', padding: 10, borderRadius: 10 }}>
                <Sparkles size={24} color="#fde047" />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>
                    Recommended Actions
                  </h3>
                  <div style={{ display: 'flex', gap: 6 }}>
                    {urgentCount > 0 && (
                      <span style={{ fontSize: '0.75rem', background: '#ef4444', color: '#fff', padding: '2px 8px', borderRadius: 999, fontWeight: 700 }}>
                        {urgentCount} URGENT
                      </span>
                    )}
                    {highCount > 0 && (
                      <span style={{ fontSize: '0.75rem', background: '#f97316', color: '#fff', padding: '2px 8px', borderRadius: 999, fontWeight: 700 }}>
                        {highCount} HIGH PRIORITY
                      </span>
                    )}
                  </div>
                </div>
                <p style={{ margin: '4px 0 0', color: '#c7d2fe', fontSize: '0.86rem' }}>
                  {pendingRecs.length} students have targeted smart recommendations generated from recent attendance and performance trends.
                </p>
              </div>
            </div>

            <button
              onClick={onNavigate ? () => onNavigate('teacher-recommendations') : undefined}
              style={{
                background: '#ffffff',
                color: '#312e81',
                border: 'none',
                padding: '9px 18px',
                borderRadius: 8,
                fontSize: '0.88rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              Review Recommendations <ArrowRight size={15} />
            </button>
          </div>
        );
      })()}

      {/* Cohort Overview Metrics */}
      <div className="grid-cols-4">
        <RiskCard
          title="High Attention"
          count={highRiskAlerts.length}
          subtitle="Immediate review recommended"
          icon={AlertCircle}
          colorClass="badge-high"
          bgLight="#fff1f2"
          textColor="#e11d48"
        />
        <RiskCard
          title="Moderate Change"
          count={medRiskAlerts.length}
          subtitle="Emerging downward trajectory"
          icon={AlertTriangle}
          colorClass="badge-medium"
          bgLight="#fffbeb"
          textColor="#d97706"
        />
        <RiskCard
          title="Stable Students"
          count={lowRiskCount}
          subtitle="Consistent with baseline"
          icon={CheckCircle2}
          colorClass="badge-low"
          bgLight="#f0fdf4"
          textColor="#16a34a"
        />
        <RiskCard
          title="Total Students"
          count={students.length}
          subtitle="Enrolled in active class"
          icon={Users}
          colorClass="badge-na"
          bgLight="#f8fafc"
          textColor="#475569"
        />
      </div>

      {/* Urgent Action Priority List */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Students Requiring Attention Today</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Ranked by combined multi-signal deviation from individual historical baselines.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: attentionAlerts.length > 0 ? '#e11d48' : '#16a34a', background: attentionAlerts.length > 0 ? '#fff1f2' : '#f0fdf4', padding: '4px 10px', borderRadius: '6px' }}>
              {attentionAlerts.length} Flagged
            </span>
            {alerts.length > 0 && (
              <button
                className="btn btn-outline"
                style={{ fontSize: '0.8rem', padding: '4px 10px' }}
                onClick={() => setShowAllCohort(!showAllCohort)}
              >
                {showAllCohort ? `Show Flagged Only (${attentionAlerts.length})` : `View All Cohort (${alerts.length})`}
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
            Loading student engagement signals...
          </div>
        ) : displayedAlerts.length === 0 ? (
          <div style={{ padding: '48px 24px', textAlign: 'center', background: '#f8fafc', borderRadius: '12px' }}>
            <CheckCircle2 size={40} color="#16a34a" style={{ margin: '0 auto 12px auto' }} />
            <h4 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#0f172a' }}>All Students On Track</h4>
            <p style={{ fontSize: '0.85rem', color: '#64748b', maxWidth: '400px', margin: '4px auto 16px auto' }}>
              No students in this class currently exhibit significant negative deviation from their historical baseline.
            </p>
            {alerts.length > 0 && (
              <button
                className="btn btn-outline"
                onClick={() => setShowAllCohort(true)}
              >
                Inspect All {alerts.length} Students
              </button>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {displayedAlerts.map((alertItem) => {
              const matchedStudent = students.find((s) => s.id === alertItem.student_id);
              const studentName = matchedStudent ? matchedStudent.name : `Student (${alertItem.student_id})`;
              const topReason = alertItem.reasons[0]?.explanation || 'Decline detected across engagement metrics';

              return (
                <div
                  key={alertItem.id}
                  style={{
                    padding: '16px 20px',
                    borderRadius: '12px',
                    border: '1px solid #e2e8f0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '16px',
                    background: alertItem.risk_level === 'HIGH' ? '#fffafb' : '#ffffff',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div
                      style={{
                        width: '44px',
                        height: '44px',
                        borderRadius: '10px',
                        background: alertItem.risk_level === 'HIGH' ? '#fee2e2' : '#fef3c7',
                        color: alertItem.risk_level === 'HIGH' ? '#b91c1c' : '#b45309',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '0.95rem',
                      }}
                    >
                      {alertItem.risk_score}
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>
                          {studentName}
                        </h4>
                        <RiskBadge level={alertItem.risk_level} score={alertItem.risk_score} showScore={false} />
                      </div>
                      <p style={{ fontSize: '0.82rem', color: '#475569', marginTop: '3px' }}>
                        <strong>Primary Indicator:</strong> {topReason}
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {matchedStudent && (
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => onOpenIntervention(matchedStudent)}
                      >
                        <GraduationCap size={14} />
                        Intervene
                      </button>
                    )}

                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => onSelectStudent(alertItem.student_id)}
                    >
                      Analyze Profile
                      <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
