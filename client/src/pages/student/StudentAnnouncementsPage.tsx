import React, { useEffect, useState } from 'react';
import { Bell, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../api/client';

interface Announcement {
  id: string; title: string; message: string; target: string;
  created_by_name: string; created_at: string; expires_at?: string;
}

const TARGET_COLORS: Record<string, { bg: string; text: string }> = {
  ALL_SCHOOL: { bg: '#eef2ff', text: '#4f46e5' },
  TEACHERS: { bg: '#fffbeb', text: '#d97706' },
  STUDENTS: { bg: '#e0f2fe', text: '#0891b2' },
  CLASS: { bg: '#f0fdf4', text: '#059669' },
  SECTION: { bg: '#fdf4ff', text: '#a855f7' },
};

export const StudentAnnouncementsPage: React.FC = () => {
  const { token } = useAuth();
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/api/v1/student/announcements', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(j => { if (j.success) setAnnouncements(j.data); })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0c4a6e', marginBottom: '4px' }}>Announcements</h1>
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Important notices and updates from your school and teachers.</p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>
          <RefreshCw size={28} color="#0891b2" style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <p>Loading announcements...</p>
        </div>
      ) : announcements.length === 0 ? (
        <div style={{ background: 'white', borderRadius: '16px', padding: '60px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
          <Bell size={40} color="#d1d5db" style={{ marginBottom: '16px' }} />
          <h3 style={{ color: '#0f172a' }}>No Announcements</h3>
          <p style={{ color: '#64748b' }}>There are no announcements for you right now.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {announcements.map(ann => {
            const colors = TARGET_COLORS[ann.target] || { bg: '#f8fafc', text: '#475569' };
            return (
              <div key={ann.id} style={{
                background: 'white', borderRadius: '16px', padding: '20px 24px',
                border: '1px solid #e2e8f0', borderLeft: `4px solid ${colors.text}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                      <h4 style={{ fontWeight: 800, color: '#0f172a', margin: 0, fontSize: '1rem' }}>{ann.title}</h4>
                      <span style={{ background: colors.bg, color: colors.text, padding: '3px 8px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 700 }}>
                        {ann.target.replace('_', ' ')}
                      </span>
                    </div>
                    <p style={{ color: '#475569', fontSize: '0.875rem', margin: '0 0 12px 0', lineHeight: 1.65 }}>{ann.message}</p>
                    <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem', color: '#94a3b8' }}>
                      <span>Posted by {ann.created_by_name}</span>
                      <span>{new Date(ann.created_at).toLocaleDateString()}</span>
                      {ann.expires_at && <span style={{ color: '#d97706' }}>⏰ Expires {ann.expires_at}</span>}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
