import React, { useEffect, useState } from 'react';
import { Bell, ChevronRight, Megaphone, Sparkles, UserCheck, Calendar, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export interface AnnouncementItem {
  id: string;
  title: string;
  message: string;
  target: 'ALL_SCHOOL' | 'TEACHERS' | 'STUDENTS' | 'CLASS' | 'SECTION' | string;
  target_class_id?: string;
  created_by_name: string;
  created_at: string;
  expires_at?: string;
}

interface AnnouncementsWidgetProps {
  compact?: boolean;
  maxItems?: number;
  onViewAll?: () => void;
}

const TARGET_TAGS: Record<string, { label: string; bg: string; text: string; border: string }> = {
  ALL_SCHOOL: { label: 'All School', bg: '#fdf2f8', text: '#db2777', border: '#fbcfe8' },
  TEACHERS: { label: 'Teachers Only', bg: '#fef3c7', text: '#b45309', border: '#fde68a' },
  STUDENTS: { label: 'Students', bg: '#e0f2fe', text: '#0369a1', border: '#bae6fd' },
  CLASS: { label: 'Class Specific', bg: '#ecfdf5', text: '#047857', border: '#a7f3d0' },
  SECTION: { label: 'Section', bg: '#f5f3ff', text: '#6d28d9', border: '#ddd6fe' },
};

export const AnnouncementsWidget: React.FC<AnnouncementsWidgetProps> = ({
  compact = false,
  maxItems = 3,
  onViewAll,
}) => {
  const { token, currentUser } = useAuth();
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAnnouncements = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const res = await fetch('/api/v1/announcements', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.success && Array.isArray(data.data)) {
        setAnnouncements(data.data);
      }
    } catch (err) {
      console.error('Error fetching announcements:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnnouncements();
  }, [token]);

  const displayList = announcements.slice(0, maxItems);

  return (
    <div
      style={{
        background: 'white',
        borderRadius: '20px',
        border: '1px solid #e2e8f0',
        padding: compact ? '20px 22px' : '24px 28px',
        boxShadow: '0 4px 20px -4px rgba(0, 0, 0, 0.05)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
          paddingBottom: '14px',
          borderBottom: '1px solid #f1f5f9',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(245, 158, 11, 0.25)',
            }}
          >
            <Megaphone size={19} color="white" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>
                Principal's Announcements
              </h3>
              <span
                style={{
                  background: '#fef3c7',
                  color: '#92400e',
                  fontSize: '0.68rem',
                  fontWeight: 800,
                  padding: '2px 8px',
                  borderRadius: '20px',
                  border: '1px solid #fde68a',
                }}
              >
                OFFICIAL
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>
              Broadcasts & institutional notices from School Administration
            </p>
          </div>
        </div>

        {onViewAll && announcements.length > maxItems && (
          <button
            onClick={onViewAll}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#d97706',
              fontSize: '0.82rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              cursor: 'pointer',
              padding: '6px 10px',
              borderRadius: '8px',
              transition: 'background 0.15s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = '#fef3c7')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            View All ({announcements.length})
            <ChevronRight size={15} />
          </button>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8' }}>
          <RefreshCw size={22} color="#f59e0b" style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }} />
          <p style={{ margin: 0, fontSize: '0.82rem' }}>Checking for latest notices...</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : announcements.length === 0 ? (
        <div
          style={{
            padding: '28px 16px',
            textAlign: 'center',
            background: '#fafafa',
            borderRadius: '12px',
            border: '1px dashed #e2e8f0',
          }}
        >
          <Bell size={28} color="#cbd5e1" style={{ marginBottom: '8px' }} />
          <p style={{ margin: 0, color: '#64748b', fontSize: '0.85rem', fontWeight: 600 }}>
            No new announcements today
          </p>
          <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '0.75rem' }}>
            All administrative communications will be posted here.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {displayList.map((ann, idx) => {
            const tag = TARGET_TAGS[ann.target] || {
              label: ann.target,
              bg: '#f1f5f9',
              text: '#475569',
              border: '#e2e8f0',
            };

            const isRecent = idx === 0;

            return (
              <div
                key={ann.id}
                style={{
                  background: isRecent ? 'linear-gradient(to right, #fffbeb, #ffffff)' : '#f8fafc',
                  borderRadius: '14px',
                  padding: '14px 18px',
                  border: isRecent ? '1px solid #fde68a' : '1px solid #e2e8f0',
                  borderLeft: isRecent ? '4px solid #f59e0b' : '4px solid #94a3b8',
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <h4 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 800, color: '#1e293b' }}>
                      {ann.title}
                    </h4>
                    {isRecent && (
                      <span
                        style={{
                          background: '#ef4444',
                          color: 'white',
                          fontSize: '0.62rem',
                          fontWeight: 800,
                          padding: '1px 6px',
                          borderRadius: '10px',
                          textTransform: 'uppercase',
                        }}
                      >
                        NEW
                      </span>
                    )}
                  </div>

                  <span
                    style={{
                      background: tag.bg,
                      color: tag.text,
                      border: `1px solid ${tag.border}`,
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '12px',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {tag.label}
                  </span>
                </div>

                <p
                  style={{
                    margin: '0 0 10px 0',
                    fontSize: '0.83rem',
                    color: '#475569',
                    lineHeight: 1.5,
                  }}
                >
                  {ann.message}
                </p>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.72rem',
                    color: '#94a3b8',
                    borderTop: '1px solid rgba(0,0,0,0.04)',
                    paddingTop: '6px',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#64748b', fontWeight: 600 }}>
                    <UserCheck size={12} color="#059669" />
                    {ann.created_by_name || 'Dr. Evelyn Reed (Principal)'}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Calendar size={12} />
                    {new Date(ann.created_at).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
