import React, { useEffect, useState } from 'react';
import { CalendarDays, CheckCircle2, Clock, RefreshCw, XCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../api/client';

export const StudentAttendancePage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/api/v1/student/attendance', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(j => { if (j.success) setData(j.data); })
      .finally(() => setLoading(false));
  }, []);

  const statusIcon = (s: string) => {
    if (s === 'PRESENT') return <CheckCircle2 size={16} color="#16a34a" />;
    if (s === 'ABSENT') return <XCircle size={16} color="#ef4444" />;
    return <Clock size={16} color="#d97706" />;
  };
  const statusColors: Record<string, { bg: string; text: string }> = {
    PRESENT: { bg: '#f0fdf4', text: '#16a34a' },
    ABSENT: { bg: '#fef2f2', text: '#ef4444' },
    LATE: { bg: '#fffbeb', text: '#d97706' },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0c4a6e', marginBottom: '4px' }}>My Attendance</h1>
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Your full attendance history. Contact your teacher if there are any errors.</p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>
          <RefreshCw size={28} color="#0891b2" style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <p>Loading attendance...</p>
        </div>
      ) : !data ? (
        <div style={{ textAlign: 'center', padding: '60px', background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
          No attendance data yet.
        </div>
      ) : (
        <>
          {/* Summary cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '16px' }}>
            {[
              { label: 'Attendance %', value: `${data.summary.attendance_percentage ?? 'N/A'}${data.summary.attendance_percentage !== null ? '%' : ''}`, color: '#0891b2', bg: '#e0f2fe' },
              { label: 'Present', value: data.summary.present, color: '#16a34a', bg: '#f0fdf4' },
              { label: 'Absent', value: data.summary.absent, color: '#ef4444', bg: '#fef2f2' },
              { label: 'Late', value: data.summary.late, color: '#d97706', bg: '#fffbeb' },
              { label: 'Total Days', value: data.summary.total, color: '#475569', bg: '#f8fafc' },
            ].map(({ label, value, color, bg }) => (
              <div key={label} style={{ background: bg, borderRadius: '14px', padding: '18px', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color }}>{value}</div>
                <div style={{ fontSize: '0.75rem', color, fontWeight: 600, marginTop: '4px' }}>{label}</div>
              </div>
            ))}
          </div>

          {/* Attendance % bar */}
          {data.summary.attendance_percentage !== null && (
            <div style={{ background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#0f172a' }}>Overall Attendance</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 800, color: data.summary.attendance_percentage >= 75 ? '#16a34a' : '#ef4444' }}>
                  {data.summary.attendance_percentage}%
                </span>
              </div>
              <div style={{ height: '12px', background: '#e2e8f0', borderRadius: '6px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%', width: `${data.summary.attendance_percentage}%`,
                  background: data.summary.attendance_percentage >= 75
                    ? 'linear-gradient(90deg, #16a34a, #22c55e)'
                    : 'linear-gradient(90deg, #ef4444, #f87171)',
                  borderRadius: '6px', transition: 'width 0.8s ease',
                }} />
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '6px' }}>
                {data.summary.attendance_percentage >= 75
                  ? '✅ Good standing (≥ 75%)'
                  : '⚠️ Below required attendance (75%)'}
              </div>
            </div>
          )}

          {/* Records table */}
          <div style={{ background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0' }}>
            <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CalendarDays size={18} color="#0891b2" /> Attendance Records
            </h3>
            {data.records.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>No records available.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '400px', overflowY: 'auto' }}>
                {[...data.records].reverse().map((r: any, i: number) => {
                  const colors = statusColors[r.status] || { bg: '#f8fafc', text: '#475569' };
                  return (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '10px 14px', borderRadius: '10px', background: colors.bg,
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {statusIcon(r.status)}
                        <span style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.875rem' }}>{r.date}</span>
                      </div>
                      <span style={{ background: 'white', color: colors.text, padding: '3px 10px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 700, border: `1px solid ${colors.text}33` }}>
                        {r.status}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
