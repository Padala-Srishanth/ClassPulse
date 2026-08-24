import React, { useEffect, useState } from 'react';
import { AlertTriangle, RefreshCw, Search } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface AbsenteeReport {
  date_filter: string | null;
  class_filter: string | null;
  report: {
    class_id: string; class_name: string; grade: string; section: string;
    absentees: { student_id: string; student_name: string; student_code: string; date: string; status: string; }[];
  }[];
  total_absentees: number;
}

export const PrincipalReportsPage: React.FC = () => {
  const { token } = useAuth();
  const [absenteeReport, setAbsenteeReport] = useState<AbsenteeReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [dateFilter, setDateFilter] = useState(new Date().toISOString().split('T')[0]);

  const loadReport = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (dateFilter) params.set('date', dateFilter);
      const res = await fetch(`/api/v1/principal/absentees?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) setAbsenteeReport(json.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadReport(); }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#064e3b', marginBottom: '4px' }}>Reports & Analytics</h1>
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Attendance reports, absentee tracking, and school analytics.</p>
      </div>

      {/* Filters */}
      <div style={{ background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0', display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div style={{ flex: '1', minWidth: '200px' }}>
          <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Date</label>
          <input
            type="date" value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            style={{
              width: '100%', padding: '10px 14px', border: '1.5px solid #e2e8f0',
              borderRadius: '10px', fontSize: '0.9rem', color: '#0f172a',
              outline: 'none', background: '#f8fafc',
            }}
          />
        </div>
        <button
          onClick={loadReport}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '10px 20px', background: '#059669', color: 'white',
            border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 600,
          }}
        >
          <Search size={16} /> Generate Report
        </button>
      </div>

      {/* Summary */}
      {absenteeReport && (
        <div style={{
          background: 'linear-gradient(135deg, #064e3b, #059669)', borderRadius: '16px', padding: '20px',
          display: 'flex', gap: '32px', color: 'white', flexWrap: 'wrap',
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', opacity: 0.8, fontWeight: 600, textTransform: 'uppercase' }}>Date</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{absenteeReport.date_filter || 'All Dates'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', opacity: 0.8, fontWeight: 600, textTransform: 'uppercase' }}>Total Absentees</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{absenteeReport.total_absentees}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', opacity: 0.8, fontWeight: 600, textTransform: 'uppercase' }}>Classes Affected</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{absenteeReport.report.length}</div>
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>
          <RefreshCw size={28} color="#059669" style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <p>Generating report...</p>
        </div>
      ) : absenteeReport && absenteeReport.report.length === 0 ? (
        <div style={{ background: 'white', borderRadius: '16px', padding: '60px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px' }}>✅</div>
          <h3 style={{ color: '#064e3b', fontWeight: 800, marginBottom: '8px' }}>Full Attendance!</h3>
          <p style={{ color: '#64748b' }}>No absentees recorded for {absenteeReport.date_filter || 'the selected period'}.</p>
        </div>
      ) : absenteeReport ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {absenteeReport.report.map((cls) => (
            <div key={cls.class_id} style={{ background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <AlertTriangle size={18} color="#d97706" />
                <h3 style={{ fontWeight: 700, color: '#0f172a', margin: 0 }}>
                  {cls.class_name} — Grade {cls.grade}-{cls.section}
                </h3>
                <span style={{ marginLeft: 'auto', background: '#fffbeb', color: '#d97706', padding: '4px 10px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 700 }}>
                  {cls.absentees.length} absent/late
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {cls.absentees.map((a) => (
                  <div key={`${a.student_id}-${a.date}`} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '10px 14px', background: a.status === 'ABSENT' ? '#fef2f2' : '#fffbeb',
                    borderRadius: '8px',
                  }}>
                    <div>
                      <span style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.875rem' }}>{a.student_name}</span>
                      <span style={{ color: '#64748b', fontSize: '0.78rem', marginLeft: '8px' }}>#{a.student_code}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                      <span style={{ color: '#64748b', fontSize: '0.78rem' }}>{a.date}</span>
                      <span style={{
                        background: a.status === 'ABSENT' ? '#fecdd3' : '#fde68a',
                        color: a.status === 'ABSENT' ? '#be123c' : '#92400e',
                        padding: '2px 8px', borderRadius: '6px', fontWeight: 700, fontSize: '0.72rem',
                      }}>
                        {a.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
};
