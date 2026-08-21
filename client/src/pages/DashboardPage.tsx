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
import { RiskAlert, SchoolClass, Student } from '../types';

interface DashboardPageProps {
  onSelectStudent: (studentId: string) => void;
  onOpenIntervention: (student: Student) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onSelectStudent,
  onOpenIntervention,
}) => {
  const { schoolId } = useAuth();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<string>('');
  const [students, setStudents] = useState<Student[]>([]);
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  // Load classes on mount
  useEffect(() => {
    async function loadClasses() {
      if (!schoolId) return;
      try {
        const clsList = await classesApi.listSchoolClasses(schoolId);
        setClasses(clsList);
        if (clsList.length > 0) {
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

  // Load class data & alerts
  useEffect(() => {
    async function loadClassData() {
      if (!selectedClassId) return;
      setLoading(true);
      try {
        const stus = await studentsApi.listClassStudents(selectedClassId);
        setStudents(stus);

        const activeAlerts = await riskApi.getClassActiveAlerts(selectedClassId);
        setAlerts(activeAlerts);
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

  const highRiskAlerts = alerts.filter((a) => a.risk_level === 'HIGH');
  const medRiskAlerts = alerts.filter((a) => a.risk_level === 'MEDIUM');
  const lowRiskCount = Math.max(0, students.length - alerts.length);

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

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
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

          <button
            className="btn btn-primary"
            onClick={handleRunClassAnalysis}
            disabled={analyzing || !selectedClassId}
          >
            <Sparkles size={16} />
            {analyzing ? 'Analyzing Cohort...' : 'Run AI Risk Detection'}
          </button>
        </div>
      </div>

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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Students Requiring Attention Today</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Ranked by combined multi-signal deviation from individual historical baselines.
            </p>
          </div>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#4f46e5', background: '#eef2ff', padding: '4px 10px', borderRadius: '6px' }}>
            {alerts.length} Flagged
          </span>
        </div>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
            Loading student engagement signals...
          </div>
        ) : alerts.length === 0 ? (
          <div style={{ padding: '48px 24px', textAlign: 'center', background: '#f8fafc', borderRadius: '12px' }}>
            <CheckCircle2 size={40} color="#16a34a" style={{ margin: '0 auto 12px auto' }} />
            <h4 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#0f172a' }}>All Students On Track</h4>
            <p style={{ fontSize: '0.85rem', color: '#64748b', maxWidth: '400px', margin: '4px auto 0 auto' }}>
              No students in this class currently exhibit significant negative deviation from their historical baseline.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {alerts.map((alertItem) => {
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
