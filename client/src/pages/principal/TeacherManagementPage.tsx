import React, { useEffect, useState } from 'react';
import { BookOpen, Mail, RefreshCw, Users } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface Teacher {
  id: string;
  name: string;
  email: string;
  status: string;
  assigned_classes: { class_id: string; class_name: string; grade: string; section: string; }[];
}

export const TeacherManagementPage: React.FC = () => {
  const { token } = useAuth();
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/principal/teachers', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(j => { if (j.success) setTeachers(j.data); })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#064e3b', marginBottom: '4px' }}>Teacher Management</h1>
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>View teachers, their class assignments, and contact information.</p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>
          <RefreshCw size={28} style={{ animation: 'spin 1s linear infinite', marginBottom: '12px', color: '#059669' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <p>Loading teachers...</p>
        </div>
      ) : teachers.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '80px', background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
          <Users size={48} color="#d1d5db" style={{ marginBottom: '16px' }} />
          <h3 style={{ color: '#0f172a', marginBottom: '8px' }}>No Teachers Found</h3>
          <p style={{ color: '#64748b' }}>No teacher accounts are registered for this school yet.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
          {teachers.map((teacher) => (
            <div
              key={teacher.id}
              style={{
                background: 'white', borderRadius: '16px', padding: '24px',
                border: '1px solid #e2e8f0', transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.boxShadow = '0 8px 24px rgba(0,0,0,0.1)';
                (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.boxShadow = 'none';
                (e.currentTarget as HTMLElement).style.transform = 'translateY(0)';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
                <div style={{
                  width: '48px', height: '48px', borderRadius: '12px',
                  background: 'linear-gradient(135deg, #059669, #10b981)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'white', fontWeight: 800, fontSize: '1.1rem', flexShrink: 0,
                }}>
                  {teacher.name.charAt(0)}
                </div>
                <div>
                  <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '1rem' }}>{teacher.name}</div>
                  <div style={{ color: '#64748b', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                    <Mail size={12} /> {teacher.email}
                  </div>
                </div>
                <span style={{
                  marginLeft: 'auto',
                  background: teacher.status === 'ACTIVE' ? '#d1fae5' : '#f1f5f9',
                  color: teacher.status === 'ACTIVE' ? '#065f46' : '#64748b',
                  padding: '3px 10px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 700,
                }}>
                  {teacher.status}
                </span>
              </div>

              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <BookOpen size={12} /> Assigned Classes
                </div>
                {teacher.assigned_classes.length === 0 ? (
                  <div style={{ color: '#94a3b8', fontSize: '0.82rem', fontStyle: 'italic' }}>No classes assigned yet</div>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {teacher.assigned_classes.map(cls => (
                      <span key={cls.class_id} style={{
                        background: '#f0fdf4', color: '#065f46',
                        padding: '4px 10px', borderRadius: '20px', fontSize: '0.78rem', fontWeight: 600,
                        border: '1px solid #bbf7d0',
                      }}>
                        {cls.class_name} ({cls.grade}-{cls.section})
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
