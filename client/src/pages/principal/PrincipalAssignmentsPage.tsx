import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  BarChart3,
  BookOpen,
  CheckCircle2,
  Clock,
  FileText,
  Percent,
  RefreshCw,
  Search,
  Users,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../api/client';

interface ClassStat {
  class_id: string;
  class_name: string;
  total_assignments: number;
  total_students: number;
  total_submissions: number;
  submission_rate: number;
  late_submissions: number;
  pending_submissions: number;
  graded_submissions: number;
}

interface SchoolStats {
  total_assignments: number;
  total_submissions: number;
  total_graded: number;
  overall_submission_rate: number;
  classes: ClassStat[];
}

export const PrincipalAssignmentsPage: React.FC = () => {
  const { token } = useAuth();
  const [stats, setStats] = useState<SchoolStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const loadStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch('/api/v1/assignments/stats/overview', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) {
        setStats(json.data);
      } else {
        setError(json.error?.message || 'Failed to load assignment statistics');
      }
    } catch (e: any) {
      setError(e.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [token]);

  const classesList = stats?.classes || [];
  const filteredClasses = classesList.filter(c =>
    c.class_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
        borderRadius: '20px', padding: '28px 32px', color: 'white', position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', top: '-30px', right: '-30px', width: '160px', height: '160px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
        <div style={{ position: 'relative' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.8, fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <BarChart3 size={16} /> Academic Monitoring
          </div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 900, margin: '6px 0 0', letterSpacing: '-0.02em' }}>
            School Assignments & Classwork Overview
          </h1>
          <p style={{ opacity: 0.75, fontSize: '0.88rem', margin: '4px 0 0' }}>
            Track school-wide assignment completion rates, evaluate teacher classwork frequency, and detect overdue cohorts.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        {[
          {
            label: 'Total Assignments',
            value: stats?.total_assignments ?? 0,
            sub: 'Published school-wide',
            icon: FileText,
            color: '#4f46e5',
            bg: '#eef2ff',
          },
          {
            label: 'Overall Submission Rate',
            value: `${stats?.overall_submission_rate ?? 0}%`,
            sub: 'Across all active classes',
            icon: Percent,
            color: '#16a34a',
            bg: '#dcfce7',
          },
          {
            label: 'Total Turned In',
            value: stats?.total_submissions ?? 0,
            sub: 'Student submissions logged',
            icon: CheckCircle2,
            color: '#0891b2',
            bg: '#e0f2fe',
          },
          {
            label: 'Total Evaluated',
            value: stats?.total_graded ?? 0,
            sub: 'Submissions graded by teachers',
            icon: BookOpen,
            color: '#d97706',
            bg: '#fef3c7',
          },
        ].map(kpi => {
          const Icon = kpi.icon;
          return (
            <div key={kpi.label} style={{
              background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0',
              display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
              boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
            }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                  {kpi.label}
                </span>
                <div style={{ fontSize: '1.75rem', fontWeight: 900, color: '#0f172a', margin: '4px 0' }}>
                  {kpi.value}
                </div>
                <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>{kpi.sub}</span>
              </div>
              <div style={{
                width: '42px', height: '42px', borderRadius: '12px', background: kpi.bg,
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: kpi.color, flexShrink: 0,
              }}>
                <Icon size={20} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Classwise Breakdown Table */}
      <div style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <div style={{
          padding: '20px 24px', borderBottom: '1px solid #e2e8f0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px',
        }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Class-Wise Assignment Engagement
            </h3>
            <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Detailed completion and overdue metrics across all {classesList.length} cohorts
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f8fafc', padding: '8px 14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
            <Search size={15} color="#94a3b8" />
            <input
              type="text"
              placeholder="Search class..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: '0.85rem' }}
            />
          </div>
        </div>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#64748b', gap: '8px' }}>
            <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite' }} /> Loading analytics...
          </div>
        ) : error ? (
          <div style={{ padding: '24px', color: '#b91c1c' }}>{error}</div>
        ) : filteredClasses.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>No class records found.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  <th style={{ padding: '14px 20px', fontWeight: 700 }}>Class</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700 }}>Assignments</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700 }}>Enrolled</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700 }}>Turned In</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700 }}>Submission Rate</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700 }}>Late</th>
                  <th style={{ padding: '14px 16px', fontWeight: 700 }}>Unsubmitted</th>
                  <th style={{ padding: '14px 20px', fontWeight: 700 }}>Graded</th>
                </tr>
              </thead>
              <tbody>
                {filteredClasses.map((cls, idx) => {
                  const rateColor =
                    cls.submission_rate >= 75 ? '#16a34a' : cls.submission_rate >= 50 ? '#d97706' : '#dc2626';

                  return (
                    <tr
                      key={cls.class_id}
                      style={{
                        borderBottom: idx === filteredClasses.length - 1 ? 'none' : '1px solid #f1f5f9',
                        transition: 'background 0.15s',
                      }}
                      onMouseEnter={e => (e.currentTarget.style.background = '#f8fafc')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'white')}
                    >
                      <td style={{ padding: '16px 20px', fontWeight: 800, color: '#0f172a' }}>
                        {cls.class_name}
                      </td>
                      <td style={{ padding: '16px 16px', color: '#334155', fontWeight: 600 }}>
                        {cls.total_assignments}
                      </td>
                      <td style={{ padding: '16px 16px', color: '#64748b' }}>
                        {cls.total_students} students
                      </td>
                      <td style={{ padding: '16px 16px', fontWeight: 700, color: '#0f172a' }}>
                        {cls.total_submissions}
                      </td>
                      <td style={{ padding: '16px 16px', minWidth: '160px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontWeight: 800, color: rateColor, width: '42px', fontSize: '0.85rem' }}>
                            {cls.submission_rate}%
                          </span>
                          <div style={{ flex: 1, height: '6px', background: '#f1f5f9', borderRadius: '999px', overflow: 'hidden' }}>
                            <div style={{
                              width: `${cls.submission_rate}%`, height: '100%',
                              background: rateColor, borderRadius: '999px',
                            }} />
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '16px 16px' }}>
                        {cls.late_submissions > 0 ? (
                          <span style={{ background: '#fee2e2', color: '#b91c1c', padding: '2px 8px', borderRadius: '12px', fontSize: '0.78rem', fontWeight: 700 }}>
                            {cls.late_submissions}
                          </span>
                        ) : (
                          <span style={{ color: '#94a3b8' }}>0</span>
                        )}
                      </td>
                      <td style={{ padding: '16px 16px' }}>
                        {cls.pending_submissions > 0 ? (
                          <span style={{ background: '#fef3c7', color: '#b45309', padding: '2px 8px', borderRadius: '12px', fontSize: '0.78rem', fontWeight: 700 }}>
                            {cls.pending_submissions}
                          </span>
                        ) : (
                          <span style={{ color: '#94a3b8' }}>0</span>
                        )}
                      </td>
                      <td style={{ padding: '16px 20px', fontWeight: 700, color: '#16a34a' }}>
                        {cls.graded_submissions}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
