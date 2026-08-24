import React, { useEffect, useState } from 'react';
import { Bell, Megaphone, Plus, Send } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

type AnnouncementTarget = 'ALL_SCHOOL' | 'TEACHERS' | 'STUDENTS' | 'CLASS' | 'SECTION';

interface Announcement {
  id: string; title: string; message: string; target: string;
  created_by_name: string; created_at: string; expires_at?: string;
}

const TARGET_OPTIONS: { value: AnnouncementTarget; label: string }[] = [
  { value: 'ALL_SCHOOL', label: '🏫 Entire School' },
  { value: 'TEACHERS', label: '👩‍🏫 Teachers Only' },
  { value: 'STUDENTS', label: '🎓 Students Only' },
];

export const AnnouncementsPage: React.FC = () => {
  const { token } = useAuth();
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    title: '', message: '',
    target: 'ALL_SCHOOL' as AnnouncementTarget,
    expires_at: '',
  });

  const loadAnnouncements = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/announcements', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) setAnnouncements(json.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { loadAnnouncements(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.message.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch('/api/v1/announcements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...form, expires_at: form.expires_at || undefined }),
      });
      const json = await res.json();
      if (json.success) {
        setForm({ title: '', message: '', target: 'ALL_SCHOOL', expires_at: '' });
        setShowForm(false);
        loadAnnouncements();
      }
    } finally { setSubmitting(false); }
  };

  const targetColors: Record<string, { bg: string; text: string }> = {
    ALL_SCHOOL: { bg: '#eef2ff', text: '#4f46e5' },
    TEACHERS: { bg: '#fffbeb', text: '#d97706' },
    STUDENTS: { bg: '#e0f2fe', text: '#0891b2' },
    CLASS: { bg: '#f0fdf4', text: '#059669' },
    SECTION: { bg: '#fdf4ff', text: '#a855f7' },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#064e3b', marginBottom: '4px' }}>Announcements</h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Send announcements to teachers, students, or the entire school.</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '10px 20px', background: showForm ? '#f1f5f9' : '#059669',
            color: showForm ? '#475569' : 'white', border: 'none',
            borderRadius: '10px', cursor: 'pointer', fontWeight: 700,
          }}
        >
          <Plus size={16} /> New Announcement
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div style={{ background: 'white', borderRadius: '16px', padding: '28px', border: '1px solid #e2e8f0', boxShadow: '0 4px 16px rgba(0,0,0,0.06)' }}>
          <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Megaphone size={18} color="#059669" /> Create Announcement
          </h3>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Title</label>
              <input
                value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}
                placeholder="Announcement title..."
                style={{ width: '100%', padding: '10px 14px', border: '1.5px solid #e2e8f0', borderRadius: '10px', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Message</label>
              <textarea
                value={form.message} onChange={e => setForm({ ...form, message: e.target.value })}
                placeholder="Announcement message..."
                rows={4}
                style={{ width: '100%', padding: '10px 14px', border: '1.5px solid #e2e8f0', borderRadius: '10px', fontSize: '0.9rem', outline: 'none', resize: 'vertical', boxSizing: 'border-box', fontFamily: 'inherit' }}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Target Audience</label>
                <select
                  value={form.target} onChange={e => setForm({ ...form, target: e.target.value as AnnouncementTarget })}
                  style={{ width: '100%', padding: '10px 14px', border: '1.5px solid #e2e8f0', borderRadius: '10px', fontSize: '0.9rem', outline: 'none', background: 'white' }}
                >
                  {TARGET_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Expires On (Optional)</label>
                <input
                  type="date" value={form.expires_at} onChange={e => setForm({ ...form, expires_at: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', border: '1.5px solid #e2e8f0', borderRadius: '10px', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box' }}
                />
              </div>
            </div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button type="button" onClick={() => setShowForm(false)}
                style={{ padding: '10px 20px', background: '#f1f5f9', color: '#475569', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 600 }}>
                Cancel
              </button>
              <button type="submit" disabled={submitting}
                style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', background: '#059669', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 700 }}>
                <Send size={16} /> {submitting ? 'Sending...' : 'Send Announcement'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Announcements List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>Loading announcements...</div>
        ) : announcements.length === 0 ? (
          <div style={{ background: 'white', borderRadius: '16px', padding: '60px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
            <Bell size={40} color="#d1d5db" style={{ marginBottom: '16px' }} />
            <h3 style={{ color: '#0f172a' }}>No Announcements Yet</h3>
            <p style={{ color: '#64748b' }}>Create your first announcement to notify teachers and students.</p>
          </div>
        ) : (
          announcements.map(ann => {
            const colors = targetColors[ann.target] || { bg: '#f8fafc', text: '#475569' };
            return (
              <div key={ann.id} style={{
                background: 'white', borderRadius: '14px', padding: '20px 24px',
                border: '1px solid #e2e8f0',
                borderLeft: `4px solid ${colors.text}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                      <h4 style={{ fontWeight: 800, color: '#0f172a', margin: 0, fontSize: '1rem' }}>{ann.title}</h4>
                      <span style={{ background: colors.bg, color: colors.text, padding: '3px 8px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 700 }}>
                        {ann.target.replace('_', ' ')}
                      </span>
                    </div>
                    <p style={{ color: '#475569', fontSize: '0.875rem', margin: '0 0 10px 0', lineHeight: 1.6 }}>{ann.message}</p>
                    <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem', color: '#94a3b8' }}>
                      <span>By: <strong>{ann.created_by_name}</strong></span>
                      <span>{new Date(ann.created_at).toLocaleDateString()}</span>
                      {ann.expires_at && <span>Expires: {ann.expires_at}</span>}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
