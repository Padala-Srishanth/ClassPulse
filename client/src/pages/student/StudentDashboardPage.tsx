import React, { useEffect, useState } from 'react';
import { Activity, BookOpen, CalendarDays, GraduationCap, RefreshCw, TrendingDown, TrendingUp } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { AnnouncementsWidget } from '../../components/AnnouncementsWidget';

interface StudentDashboardPageProps {
  onNavigate?: (page: string) => void;
}

export const StudentDashboardPage: React.FC<StudentDashboardPageProps> = ({ onNavigate }) => {
  const { token, currentUser } = useAuth();
  const [attendance, setAttendance] = useState<any>(null);
  const [marks, setMarks] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [attRes, marksRes] = await Promise.all([
          fetch('/api/v1/student/attendance', { headers: { Authorization: `Bearer ${token}` } }),
          fetch('/api/v1/student/marks', { headers: { Authorization: `Bearer ${token}` } }),
        ]);
        const [attJson, marksJson] = await Promise.all([attRes.json(), marksRes.json()]);
        if (attJson.success) setAttendance(attJson.data);
        if (marksJson.success) setMarks(marksJson.data);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px', flexDirection: 'column', gap: '16px' }}>
        <RefreshCw size={32} color="#0891b2" style={{ animation: 'spin 1s linear infinite' }} />
        <p style={{ color: '#64748b' }}>Loading your dashboard...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  const attSummary = attendance?.summary;
  const recentMarks = marks?.results?.slice(-3) || [];
  const avgPct = marks?.average_percentage;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Welcome banner */}
      <div style={{
        background: 'linear-gradient(135deg, #0c4a6e 0%, #0891b2 100%)',
        borderRadius: '20px', padding: '32px 36px', color: 'white',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', top: '-30px', right: '-30px', width: '180px', height: '180px', borderRadius: '50%', background: 'rgba(255,255,255,0.06)' }} />
        <div style={{ position: 'absolute', bottom: '-40px', right: '100px', width: '120px', height: '120px', borderRadius: '50%', background: 'rgba(255,255,255,0.04)' }} />
        <div style={{ position: 'relative' }}>
          <p style={{ opacity: 0.7, fontSize: '0.85rem', margin: '0 0 6px 0', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Welcome back</p>
          <h1 style={{ fontSize: '2rem', fontWeight: 900, margin: '0 0 8px 0', letterSpacing: '-0.02em' }}>
            {currentUser?.name?.replace(' (Student)', '') || 'Student'} 👋
          </h1>
          <p style={{ opacity: 0.8, fontSize: '0.9rem', margin: 0 }}>
            Here's your academic summary for today.
          </p>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
        {[
          {
            label: 'Attendance',
            value: attSummary?.attendance_percentage !== null && attSummary?.attendance_percentage !== undefined
              ? `${attSummary.attendance_percentage}%` : 'N/A',
            sub: `${attSummary?.present || 0} present, ${attSummary?.absent || 0} absent`,
            icon: CalendarDays, color: '#0891b2', bg: '#e0f2fe',
          },
          {
            label: 'Avg Score',
            value: avgPct !== null && avgPct !== undefined ? `${avgPct}%` : 'N/A',
            sub: `${marks?.total_exams || 0} exams`,
            icon: GraduationCap, color: '#4f46e5', bg: '#eef2ff',
          },
          {
            label: 'Days Present',
            value: attSummary?.present || 0,
            sub: `out of ${attSummary?.total || 0} days`,
            icon: Activity, color: '#059669', bg: '#d1fae5',
          },
          {
            label: 'Days Absent',
            value: attSummary?.absent || 0,
            sub: `${attSummary?.late || 0} late`,
            icon: TrendingDown, color: '#ef4444', bg: '#fef2f2',
          },
        ].map(({ label, value, sub, icon: Icon, color, bg }) => (
          <div key={label} style={{
            background: 'white', borderRadius: '16px', padding: '20px',
            border: '1px solid #e2e8f0',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <p style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', margin: '0 0 6px 0' }}>{label}</p>
                <p style={{ fontSize: '1.8rem', fontWeight: 800, color, margin: '0 0 4px 0', lineHeight: 1 }}>{value}</p>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: 0 }}>{sub}</p>
              </div>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={20} color={color} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Announcements from Principal */}
      <AnnouncementsWidget
        compact={true}
        maxItems={2}
        onViewAll={onNavigate ? () => onNavigate('student-announcements') : undefined}
      />

      {/* Recent marks */}
      <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
        <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '16px', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BookOpen size={18} color="#0891b2" /> Recent Exam Results
        </h3>
        {recentMarks.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
            No exam results yet. Your marks will appear here after your teacher enters them.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {recentMarks.map((r: any, i: number) => {
              const gradeColors: Record<string, string> = { 'A+': '#16a34a', 'A': '#22c55e', 'B': '#2563eb', 'C': '#d97706', 'D': '#ea580c', 'F': '#dc2626' };
              const gradeColor = gradeColors[r.grade] || '#64748b';
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '14px 18px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0',
                }}>
                  <div>
                    <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.9rem' }}>{r.exam_name}</div>
                    <div style={{ color: '#64748b', fontSize: '0.78rem', marginTop: '2px' }}>
                      {r.subject} • {r.exam_date}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{r.obtained_marks}/{r.max_marks}</div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: gradeColor }}>
                        {r.percentage.toFixed(1)}%
                      </div>
                    </div>
                    <div style={{
                      width: '40px', height: '40px', borderRadius: '10px',
                      background: gradeColor + '18',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '1rem', fontWeight: 800, color: gradeColor,
                    }}>
                      {r.grade}
                    </div>
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
