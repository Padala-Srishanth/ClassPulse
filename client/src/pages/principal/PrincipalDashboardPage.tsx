import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  BarChart3,
  BookOpen,
  CheckCircle2,
  GraduationCap,
  RefreshCw,
  Shield,
  TrendingDown,
  TrendingUp,
  Users,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface ClassSummary {
  class_id: string;
  class_name: string;
  grade: string;
  section: string;
  student_count: number;
  high_risk_count: number;
  medium_risk_count: number;
  teacher_ids: string[];
}

interface DashboardData {
  school_id: string;
  total_classes: number;
  total_students: number;
  total_teachers: number;
  high_risk_students: number;
  medium_risk_students: number;
  low_risk_students: number;
  active_interventions: number;
  class_summaries: ClassSummary[];
}

const StatCard: React.FC<{
  title: string; value: number | string; subtitle: string;
  icon: React.FC<any>; bgColor: string; textColor: string; iconBg: string;
}> = ({ title, value, subtitle, icon: Icon, bgColor, textColor, iconBg }) => (
  <div style={{
    background: 'white', borderRadius: '16px', padding: '24px',
    border: '1px solid #e2e8f0',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
  }}
    onMouseEnter={(e) => {
      (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)';
      (e.currentTarget as HTMLElement).style.boxShadow = '0 8px 24px rgba(0,0,0,0.1)';
    }}
    onMouseLeave={(e) => {
      (e.currentTarget as HTMLElement).style.transform = 'translateY(0)';
      (e.currentTarget as HTMLElement).style.boxShadow = '0 1px 3px rgba(0,0,0,0.06)';
    }}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <p style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 8px 0' }}>
          {title}
        </p>
        <p style={{ fontSize: '2.2rem', fontWeight: 800, color: textColor, margin: '0 0 4px 0', lineHeight: 1 }}>
          {value}
        </p>
        <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: 0 }}>{subtitle}</p>
      </div>
      <div style={{
        width: '48px', height: '48px', borderRadius: '12px',
        background: iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon size={22} color={textColor} />
      </div>
    </div>
  </div>
);

export const PrincipalDashboardPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/principal/dashboard', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) {
        setData(json.data);
      } else {
        setError(json.error?.message || 'Failed to load dashboard');
      }
    } catch (e: any) {
      setError(e.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadDashboard(); }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px', flexDirection: 'column', gap: '16px' }}>
        <RefreshCw size={32} color="#059669" style={{ animation: 'spin 1s linear infinite' }} />
        <p style={{ color: '#64748b' }}>Loading school overview...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <AlertCircle size={40} color="#ef4444" style={{ marginBottom: '16px' }} />
        <p style={{ color: '#ef4444', fontWeight: 600 }}>{error || 'No data available'}</p>
        <button
          onClick={loadDashboard}
          style={{ marginTop: '16px', padding: '10px 20px', background: '#059669', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
        >
          Retry
        </button>
      </div>
    );
  }

  const totalRisk = data.high_risk_students + data.medium_risk_students + data.low_risk_students;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#064e3b', margin: '0 0 4px 0' }}>
            🏫 School Overview
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem', margin: 0 }}>
            How is the entire school performing today?
          </p>
        </div>
        <button
          onClick={loadDashboard}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '10px 18px', background: '#059669', color: 'white',
            border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem',
          }}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Top Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <StatCard title="Total Students" value={data.total_students} subtitle="Across all classes" icon={Users} bgColor="" textColor="#0f172a" iconBg="#f1f5f9" />
        <StatCard title="Total Teachers" value={data.total_teachers} subtitle="Active staff" icon={BookOpen} bgColor="" textColor="#4f46e5" iconBg="#eef2ff" />
        <StatCard title="Total Classes" value={data.total_classes} subtitle="Active sections" icon={GraduationCap} bgColor="" textColor="#0891b2" iconBg="#e0f2fe" />
        <StatCard title="Active Interventions" value={data.active_interventions} subtitle="In progress" icon={Shield} bgColor="" textColor="#d97706" iconBg="#fffbeb" />
      </div>

      {/* Risk Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
        <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 size={18} color="#059669" /> Student Risk Distribution
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {[
              { label: 'High Risk', count: data.high_risk_students, color: '#ef4444', bg: '#fef2f2', icon: AlertCircle },
              { label: 'Medium Risk', count: data.medium_risk_students, color: '#d97706', bg: '#fffbeb', icon: AlertTriangle },
              { label: 'Low Risk / Stable', count: data.low_risk_students, color: '#16a34a', bg: '#f0fdf4', icon: CheckCircle2 },
            ].map(({ label, count, color, bg, icon: Icon }) => (
              <div key={label} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '12px 16px', borderRadius: '10px', background: bg,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Icon size={16} color={color} />
                  <span style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.875rem' }}>{label}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.4rem', fontWeight: 800, color }}>{count}</span>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    {totalRisk > 0 ? `${Math.round(count / totalRisk * 100)}%` : ''}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Mini bar */}
          {totalRisk > 0 && (
            <div style={{ marginTop: '16px' }}>
              <div style={{ height: '8px', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
                <div style={{ width: `${data.high_risk_students / totalRisk * 100}%`, background: '#ef4444', transition: 'width 0.6s ease' }} />
                <div style={{ width: `${data.medium_risk_students / totalRisk * 100}%`, background: '#f59e0b', transition: 'width 0.6s ease' }} />
                <div style={{ width: `${data.low_risk_students / totalRisk * 100}%`, background: '#22c55e', transition: 'width 0.6s ease' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.72rem', color: '#94a3b8' }}>
                <span>High</span><span>Medium</span><span>Low</span>
              </div>
            </div>
          )}
        </div>

        {/* Class comparison table */}
        <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GraduationCap size={18} color="#059669" /> Class-by-Class Overview
          </h3>
          {data.class_summaries.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
              No classes found. Create classes to see the overview.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                    {['Class', 'Students', 'High Risk', 'Med Risk', 'Teachers'].map(h => (
                      <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#64748b', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.class_summaries.map((cls, i) => (
                    <tr key={cls.class_id} style={{ borderBottom: '1px solid #f1f5f9', background: i % 2 === 0 ? 'white' : '#fafafa' }}>
                      <td style={{ padding: '12px', fontWeight: 700, color: '#0f172a' }}>
                        {cls.class_name} <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 400 }}>({cls.grade}-{cls.section})</span>
                      </td>
                      <td style={{ padding: '12px', color: '#475569', fontWeight: 600 }}>{cls.student_count}</td>
                      <td style={{ padding: '12px' }}>
                        {cls.high_risk_count > 0 ? (
                          <span style={{ background: '#fef2f2', color: '#dc2626', padding: '3px 8px', borderRadius: '6px', fontWeight: 700, fontSize: '0.78rem' }}>
                            {cls.high_risk_count}
                          </span>
                        ) : <span style={{ color: '#94a3b8' }}>—</span>}
                      </td>
                      <td style={{ padding: '12px' }}>
                        {cls.medium_risk_count > 0 ? (
                          <span style={{ background: '#fffbeb', color: '#d97706', padding: '3px 8px', borderRadius: '6px', fontWeight: 700, fontSize: '0.78rem' }}>
                            {cls.medium_risk_count}
                          </span>
                        ) : <span style={{ color: '#94a3b8' }}>—</span>}
                      </td>
                      <td style={{ padding: '12px', color: '#64748b', fontSize: '0.78rem' }}>
                        {cls.teacher_ids.length > 0 ? `${cls.teacher_ids.length} assigned` : 'Unassigned'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Quick links */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        {[
          { label: 'View Absentee Report', color: '#ef4444', bg: '#fef2f2' },
          { label: 'Class Performance Report', color: '#4f46e5', bg: '#eef2ff' },
          { label: 'Teacher Assignments', color: '#059669', bg: '#d1fae5' },
          { label: 'Send Announcement', color: '#d97706', bg: '#fffbeb' },
        ].map(({ label, color, bg }) => (
          <div key={label} style={{
            background: bg, borderRadius: '12px', padding: '16px 20px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            cursor: 'pointer', border: `1px solid ${color}22`,
            transition: 'transform 0.15s ease',
          }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = 'translateY(0)'; }}
          >
            <span style={{ fontWeight: 700, color, fontSize: '0.875rem' }}>{label}</span>
            <span style={{ color, fontSize: '1rem' }}>→</span>
          </div>
        ))}
      </div>
    </div>
  );
};
