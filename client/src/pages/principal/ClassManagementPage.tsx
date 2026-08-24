import React, { useEffect, useState } from 'react';
import { AlertCircle, BookOpen, ChevronRight, GraduationCap, RefreshCw, Users } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface ClassData {
  class_id: string;
  name: string;
  grade: string;
  section: string;
  academic_year: string;
  student_count: number;
  teacher_ids: string[];
  status: string;
}

export const ClassManagementPage: React.FC = () => {
  const { token } = useAuth();
  const [classes, setClasses] = useState<ClassData[]>([]);
  const [selectedClass, setSelectedClass] = useState<string | null>(null);
  const [classReport, setClassReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    fetch('/api/v1/principal/classes', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(j => { if (j.success) setClasses(j.data); })
      .finally(() => setLoading(false));
  }, []);

  const loadClassReport = async (classId: string) => {
    setSelectedClass(classId);
    setReportLoading(true);
    try {
      const res = await fetch(`/api/v1/principal/classes/${classId}/report`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) setClassReport(json.data);
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#064e3b', marginBottom: '4px' }}>Class Management</h1>
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>View and manage all classes, sections, and their performance.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selectedClass ? '320px 1fr' : '1fr', gap: '20px' }}>
        {/* Class list */}
        <div style={{ background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BookOpen size={18} color="#059669" /> All Classes
          </h3>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>Loading...</div>
          ) : classes.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>No classes found.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {classes.map(cls => (
                <button
                  key={cls.class_id}
                  onClick={() => loadClassReport(cls.class_id)}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '14px 16px', borderRadius: '12px', border: 'none', cursor: 'pointer',
                    background: selectedClass === cls.class_id ? '#d1fae5' : '#f8fafc',
                    transition: 'all 0.15s ease', textAlign: 'left',
                  }}
                  onMouseEnter={(e) => { if (selectedClass !== cls.class_id) (e.currentTarget as HTMLElement).style.background = '#f1f5f9'; }}
                  onMouseLeave={(e) => { if (selectedClass !== cls.class_id) (e.currentTarget as HTMLElement).style.background = '#f8fafc'; }}
                >
                  <div>
                    <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.9rem' }}>{cls.name}</div>
                    <div style={{ color: '#64748b', fontSize: '0.78rem', marginTop: '2px' }}>
                      Grade {cls.grade} • Section {cls.section} • {cls.student_count} students
                    </div>
                  </div>
                  <ChevronRight size={16} color={selectedClass === cls.class_id ? '#059669' : '#94a3b8'} />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Class Report Panel */}
        {selectedClass && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {reportLoading ? (
              <div style={{ background: 'white', borderRadius: '16px', padding: '60px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
                <RefreshCw size={28} color="#059669" style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }} />
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                <p style={{ color: '#64748b' }}>Loading class report...</p>
              </div>
            ) : classReport ? (
              <>
                {/* Header */}
                <div style={{ background: 'linear-gradient(135deg, #059669, #047857)', borderRadius: '16px', padding: '24px', color: 'white' }}>
                  <h2 style={{ fontWeight: 800, fontSize: '1.4rem', margin: '0 0 4px 0' }}>
                    {classReport.class_name} — Grade {classReport.grade}-{classReport.section}
                  </h2>
                  <p style={{ opacity: 0.8, fontSize: '0.9rem', margin: 0 }}>{classReport.student_count} students enrolled</p>
                </div>

                {/* Risk dist */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                  {[
                    { label: 'High Risk', value: classReport.risk_distribution?.high || 0, color: '#ef4444', bg: '#fef2f2' },
                    { label: 'Medium Risk', value: classReport.risk_distribution?.medium || 0, color: '#d97706', bg: '#fffbeb' },
                    { label: 'Stable', value: classReport.risk_distribution?.low || 0, color: '#16a34a', bg: '#f0fdf4' },
                  ].map(({ label, value, color, bg }) => (
                    <div key={label} style={{ background: bg, borderRadius: '12px', padding: '16px', textAlign: 'center' }}>
                      <div style={{ fontSize: '2rem', fontWeight: 800, color }}>{value}</div>
                      <div style={{ fontSize: '0.78rem', color, fontWeight: 600 }}>{label}</div>
                    </div>
                  ))}
                </div>

                {/* Attendance table */}
                {classReport.attendance_summary?.length > 0 && (
                  <div style={{ background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0' }}>
                    <h3 style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Users size={16} color="#059669" /> Attendance Summary
                    </h3>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                        <thead>
                          <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                            {['Student', 'Present', 'Absent', 'Late', 'Attendance %'].map(h => (
                              <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#64748b', fontWeight: 600, fontSize: '0.72rem', textTransform: 'uppercase' }}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {classReport.attendance_summary.map((row: any, i: number) => (
                            <tr key={row.student_id} style={{ borderBottom: '1px solid #f1f5f9', background: i % 2 === 0 ? 'white' : '#fafafa' }}>
                              <td style={{ padding: '10px 12px', fontWeight: 600, color: '#0f172a' }}>{row.student_name}</td>
                              <td style={{ padding: '10px 12px', color: '#16a34a', fontWeight: 600 }}>{row.present}</td>
                              <td style={{ padding: '10px 12px', color: '#ef4444', fontWeight: 600 }}>{row.absent}</td>
                              <td style={{ padding: '10px 12px', color: '#d97706', fontWeight: 600 }}>{row.late}</td>
                              <td style={{ padding: '10px 12px' }}>
                                {row.attendance_pct !== null ? (
                                  <span style={{
                                    background: row.attendance_pct >= 75 ? '#f0fdf4' : '#fef2f2',
                                    color: row.attendance_pct >= 75 ? '#16a34a' : '#ef4444',
                                    padding: '3px 8px', borderRadius: '6px', fontWeight: 700,
                                  }}>
                                    {row.attendance_pct}%
                                  </span>
                                ) : '—'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Exam performance */}
                {classReport.exam_summaries?.length > 0 && (
                  <div style={{ background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0' }}>
                    <h3 style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <GraduationCap size={16} color="#059669" /> Exam Performance
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {classReport.exam_summaries.map((exam: any) => (
                        <div key={exam.exam_id} style={{ padding: '14px 16px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <div style={{ fontWeight: 700, color: '#0f172a' }}>{exam.exam_name} — {exam.subject}</div>
                              <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
                                {exam.exam_date} • {exam.student_count} students
                              </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: exam.average_percentage >= 60 ? '#16a34a' : '#ef4444' }}>
                                {exam.average_percentage}%
                              </div>
                              <div style={{ fontSize: '0.72rem', color: '#64748b' }}>Avg</div>
                            </div>
                          </div>
                          <div style={{ display: 'flex', gap: '16px', marginTop: '10px', fontSize: '0.78rem', color: '#64748b' }}>
                            <span>Highest: <strong style={{ color: '#16a34a' }}>{exam.highest}%</strong></span>
                            <span>Lowest: <strong style={{ color: '#ef4444' }}>{exam.lowest}%</strong></span>
                            <span>Pass: <strong style={{ color: '#4f46e5' }}>{exam.pass_count}/{exam.student_count}</strong></span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
};
