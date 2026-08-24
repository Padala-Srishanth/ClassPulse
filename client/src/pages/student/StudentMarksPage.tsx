import React, { useEffect, useState } from 'react';
import { BookOpen, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../api/client';

const GRADE_COLORS: Record<string, { bg: string; color: string }> = {
  'A+': { bg: '#dcfce7', color: '#15803d' },
  'A':  { bg: '#f0fdf4', color: '#16a34a' },
  'B':  { bg: '#eff6ff', color: '#2563eb' },
  'C':  { bg: '#fffbeb', color: '#d97706' },
  'D':  { bg: '#fff7ed', color: '#ea580c' },
  'F':  { bg: '#fef2f2', color: '#dc2626' },
};

export const StudentMarksPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/api/v1/student/marks', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(j => { if (j.success) setData(j.data); })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0c4a6e', marginBottom: '4px' }}>My Marks</h1>
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Your exam results, grades, and performance history.</p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>
          <RefreshCw size={28} color="#0891b2" style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <p>Loading your marks...</p>
        </div>
      ) : !data ? (
        <div style={{ textAlign: 'center', padding: '60px', background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0' }}>No marks yet.</div>
      ) : (
        <>
          {/* Summary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '16px' }}>
            {[
              { label: 'Total Exams', value: data.total_exams, color: '#0891b2', bg: '#e0f2fe' },
              { label: 'Average Score', value: data.average_percentage !== null ? `${data.average_percentage}%` : 'N/A', color: '#4f46e5', bg: '#eef2ff' },
            ].map(({ label, value, color, bg }) => (
              <div key={label} style={{ background: bg, borderRadius: '14px', padding: '20px', textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', fontWeight: 800, color }}>{value}</div>
                <div style={{ fontSize: '0.78rem', color, fontWeight: 600, marginTop: '4px' }}>{label}</div>
              </div>
            ))}
          </div>

          {/* Results */}
          {data.results.length === 0 ? (
            <div style={{ background: 'white', borderRadius: '16px', padding: '60px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
              <BookOpen size={40} color="#d1d5db" style={{ marginBottom: '16px' }} />
              <h3 style={{ color: '#0f172a' }}>No Exam Results Yet</h3>
              <p style={{ color: '#64748b' }}>Your teacher hasn't entered any exam results yet.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {data.results.map((r: any, i: number) => {
                const gc = GRADE_COLORS[r.grade] || { bg: '#f8fafc', color: '#475569' };
                return (
                  <div key={i} style={{
                    background: 'white', borderRadius: '16px', padding: '20px 24px',
                    border: '1px solid #e2e8f0',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '20px', flexWrap: 'wrap',
                  }}>
                    <div style={{ flex: 1, minWidth: '200px' }}>
                      <h4 style={{ fontWeight: 800, color: '#0f172a', margin: '0 0 4px 0', fontSize: '1rem' }}>{r.exam_name}</h4>
                      <div style={{ color: '#64748b', fontSize: '0.82rem' }}>
                        {r.subject} • {r.exam_date}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexShrink: 0 }}>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Marks</div>
                        <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '1rem' }}>
                          {r.obtained_marks}<span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>/{r.max_marks}</span>
                        </div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Score</div>
                        <div style={{ fontWeight: 800, color: '#0f172a', fontSize: '1.1rem' }}>{r.percentage.toFixed(1)}%</div>
                      </div>
                      <div style={{
                        width: '56px', height: '56px', borderRadius: '14px',
                        background: gc.bg, display: 'flex', alignItems: 'center',
                        justifyContent: 'center', fontSize: '1.4rem', fontWeight: 900, color: gc.color,
                      }}>
                        {r.grade}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
};
