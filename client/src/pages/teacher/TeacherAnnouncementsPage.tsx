import React, { useEffect, useState } from 'react';
import { Bell, Calendar, Megaphone, RefreshCw, Sparkles, UserCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { AnnouncementItem } from '../../components/AnnouncementsWidget';
import { apiFetch } from '../../api/client';

const TARGET_TAGS: Record<string, { label: string; bg: string; text: string; border: string }> = {
  ALL_SCHOOL: { label: 'All School', bg: '#fdf2f8', text: '#db2777', border: '#fbcfe8' },
  TEACHERS: { label: 'Teachers Only', bg: '#fef3c7', text: '#b45309', border: '#fde68a' },
  STUDENTS: { label: 'Students', bg: '#e0f2fe', text: '#0369a1', border: '#bae6fd' },
  CLASS: { label: 'Class Specific', bg: '#ecfdf5', text: '#047857', border: '#a7f3d0' },
  SECTION: { label: 'Section', bg: '#f5f3ff', text: '#6d28d9', border: '#ddd6fe' },
};

export const TeacherAnnouncementsPage: React.FC = () => {
  const { token } = useAuth();
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'TEACHERS' | 'ALL_SCHOOL'>('ALL');

  const fetchAnnouncements = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const res = await apiFetch('/api/v1/announcements', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.success && Array.isArray(data.data)) {
        setAnnouncements(data.data);
      }
    } catch (err) {
      console.error('Error fetching teacher announcements:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnnouncements();
  }, [token]);

  const filteredAnnouncements = announcements.filter((a) => {
    if (filter === 'ALL') return true;
    return a.target === filter;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)',
          borderRadius: '20px',
          padding: '28px 32px',
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 10px 25px -5px rgba(49, 46, 129, 0.2)',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: '-20px',
            right: '-20px',
            width: '160px',
            height: '160px',
            borderRadius: '50%',
            background: 'rgba(255, 255, 255, 0.05)',
          }}
        />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Megaphone size={18} color="#f59e0b" />
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#fde68a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Staff Communications Hub
            </span>
          </div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, margin: '0 0 8px 0', letterSpacing: '-0.01em' }}>
            Principal & School Announcements
          </h1>
          <p style={{ margin: 0, fontSize: '0.9rem', color: '#c7d2fe', maxWidth: '600px' }}>
            Institutional notices, curriculum reminders, and administrative circulars issued by Principal Dr. Evelyn Reed.
          </p>
        </div>
      </div>

      {/* Filters & Count */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {(['ALL', 'ALL_SCHOOL', 'TEACHERS'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              style={{
                padding: '8px 16px',
                borderRadius: '10px',
                border: filter === t ? '1px solid #4f46e5' : '1px solid #e2e8f0',
                background: filter === t ? '#eef2ff' : 'white',
                color: filter === t ? '#4f46e5' : '#64748b',
                fontWeight: filter === t ? 700 : 500,
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {t === 'ALL' ? 'All Notices' : t === 'ALL_SCHOOL' ? 'School-Wide' : 'Faculty Only'}
            </button>
          ))}
        </div>

        <button
          onClick={fetchAnnouncements}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'white',
            border: '1px solid #e2e8f0',
            padding: '8px 14px',
            borderRadius: '10px',
            color: '#475569',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={14} className={loading ? 'spin-anim' : ''} />
          Refresh
        </button>
      </div>

      {/* Announcements List */}
      {loading ? (
        <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}>
          <RefreshCw size={28} color="#6366f1" style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }} />
          <p style={{ margin: 0 }}>Loading announcements...</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : filteredAnnouncements.length === 0 ? (
        <div
          style={{
            background: 'white',
            borderRadius: '16px',
            padding: '60px 20px',
            textAlign: 'center',
            border: '1px solid #e2e8f0',
          }}
        >
          <Bell size={40} color="#cbd5e1" style={{ marginBottom: '12px' }} />
          <h3 style={{ margin: '0 0 6px 0', color: '#1e293b' }}>No Announcements Found</h3>
          <p style={{ margin: 0, color: '#64748b', fontSize: '0.88rem' }}>
            There are currently no active announcements matching your filter.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {filteredAnnouncements.map((ann) => {
            const tag = TARGET_TAGS[ann.target] || {
              label: ann.target,
              bg: '#f1f5f9',
              text: '#475569',
              border: '#e2e8f0',
            };

            return (
              <div
                key={ann.id}
                style={{
                  background: 'white',
                  borderRadius: '16px',
                  padding: '22px 26px',
                  border: '1px solid #e2e8f0',
                  boxShadow: '0 2px 10px rgba(0, 0, 0, 0.03)',
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px', gap: '12px', flexWrap: 'wrap' }}>
                  <div>
                    <h3 style={{ margin: '0 0 6px 0', fontSize: '1.08rem', fontWeight: 800, color: '#0f172a' }}>
                      {ann.title}
                    </h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.78rem', color: '#64748b' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontWeight: 600, color: '#059669' }}>
                        <UserCheck size={14} />
                        {ann.created_by_name || 'Dr. Evelyn Reed (Principal)'}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <Calendar size={14} />
                        {new Date(ann.created_at).toLocaleDateString(undefined, {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </span>
                    </div>
                  </div>

                  <span
                    style={{
                      background: tag.bg,
                      color: tag.text,
                      border: `1px solid ${tag.border}`,
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '3px 10px',
                      borderRadius: '20px',
                    }}
                  >
                    {tag.label}
                  </span>
                </div>

                <p style={{ margin: 0, fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }}>
                  {ann.message}
                </p>

                {ann.expires_at && (
                  <div style={{ marginTop: '12px', fontSize: '0.75rem', color: '#d97706', fontWeight: 600 }}>
                    ⏰ Notice active until: {ann.expires_at}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
