import React, { useEffect, useState } from 'react';
import { Calendar, MessageCircle, RefreshCw, Send } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../api/client';

interface MeetingRequest {
  id: string; meeting_type: string; subject: string; status: string;
  requested_to_name: string; proposed_date: string; created_at: string;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  PENDING: { bg: '#fffbeb', text: '#d97706' },
  ACCEPTED: { bg: '#f0fdf4', text: '#16a34a' },
  DECLINED: { bg: '#fef2f2', text: '#ef4444' },
  COMPLETED: { bg: '#eef2ff', text: '#4f46e5' },
  CANCELLED: { bg: '#f8fafc', text: '#64748b' },
};

export const StudentMessagesPage: React.FC = () => {
  const { token } = useAuth();
  const [requests, setRequests] = useState<MeetingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    subject: '', message: '', proposed_date: '',
    requested_to: 'teacher-uid-001', requested_to_name: 'Ms. Sarah Jenkins',
    meeting_type: 'STUDENT_TEACHER',
  });

  const loadRequests = () => {
    apiFetch('/api/v1/student/meeting-requests', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(j => { if (j.success) setRequests(j.data); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadRequests(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.subject || !form.message || !form.proposed_date) return;
    setSubmitting(true);
    try {
      const params = new URLSearchParams({
        subject: form.subject, message: form.message,
        proposed_date: form.proposed_date,
        requested_to: form.requested_to,
        requested_to_name: form.requested_to_name,
        meeting_type: form.meeting_type,
      });
      const res = await apiFetch(`/api/v1/student/meeting-requests?${params}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) {
        setForm({ subject: '', message: '', proposed_date: '', requested_to: 'teacher-uid-001', requested_to_name: 'Ms. Sarah Jenkins', meeting_type: 'STUDENT_TEACHER' });
        setShowForm(false);
        loadRequests();
      }
    } finally { setSubmitting(false); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0c4a6e', marginBottom: '4px' }}>Meeting Requests</h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Request a meeting with your teacher or principal.</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '10px 20px', background: showForm ? '#f1f5f9' : '#0891b2',
            color: showForm ? '#475569' : 'white', border: 'none',
            borderRadius: '10px', cursor: 'pointer', fontWeight: 700,
          }}
        >
          <MessageCircle size={16} /> Request Meeting
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div style={{ background: 'white', borderRadius: '16px', padding: '28px', border: '1px solid #bae6fd', boxShadow: '0 4px 16px rgba(14,165,233,0.08)' }}>
          <h3 style={{ fontWeight: 700, color: '#0c4a6e', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calendar size={18} color="#0891b2" /> Request a Meeting
          </h3>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Who would you like to meet?</label>
                <select
                  value={form.meeting_type}
                  onChange={e => {
                    const isTeacher = e.target.value === 'STUDENT_TEACHER';
                    setForm({
                      ...form, meeting_type: e.target.value,
                      requested_to: isTeacher ? 'teacher-uid-001' : 'sadmin-uid-001',
                      requested_to_name: isTeacher ? 'Ms. Sarah Jenkins' : 'Dr. Evelyn Reed',
                    });
                  }}
                  style={{ width: '100%', padding: '10px 14px', border: '1.5px solid #bae6fd', borderRadius: '10px', fontSize: '0.9rem', outline: 'none', background: 'white' }}
                >
                  <option value="STUDENT_TEACHER">👩‍🏫 My Teacher</option>
                  <option value="STUDENT_PRINCIPAL">🏫 Principal</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Proposed Date</label>
                <input
                  type="date" value={form.proposed_date} required
                  onChange={e => setForm({ ...form, proposed_date: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', border: '1.5px solid #bae6fd', borderRadius: '10px', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box' }}
                />
              </div>
            </div>
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Subject</label>
              <input
                value={form.subject} required onChange={e => setForm({ ...form, subject: e.target.value })}
                placeholder="Meeting subject..."
                style={{ width: '100%', padding: '10px 14px', border: '1.5px solid #bae6fd', borderRadius: '10px', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Message</label>
              <textarea
                value={form.message} required onChange={e => setForm({ ...form, message: e.target.value })}
                placeholder="Why would you like to meet?"
                rows={3}
                style={{ width: '100%', padding: '10px 14px', border: '1.5px solid #bae6fd', borderRadius: '10px', fontSize: '0.9rem', outline: 'none', resize: 'vertical', boxSizing: 'border-box', fontFamily: 'inherit' }}
              />
            </div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button type="button" onClick={() => setShowForm(false)}
                style={{ padding: '10px 20px', background: '#f1f5f9', color: '#475569', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 600 }}>
                Cancel
              </button>
              <button type="submit" disabled={submitting}
                style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', background: '#0891b2', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 700 }}>
                <Send size={16} /> {submitting ? 'Sending...' : 'Send Request'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Requests list */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>
          <RefreshCw size={28} color="#0891b2" style={{ animation: 'spin 1s linear infinite' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : requests.length === 0 ? (
        <div style={{ background: 'white', borderRadius: '16px', padding: '60px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
          <MessageCircle size={40} color="#d1d5db" style={{ marginBottom: '16px' }} />
          <h3 style={{ color: '#0f172a' }}>No Meeting Requests</h3>
          <p style={{ color: '#64748b' }}>You haven't requested any meetings yet.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {requests.map(req => {
            const colors = STATUS_COLORS[req.status] || { bg: '#f8fafc', text: '#64748b' };
            return (
              <div key={req.id} style={{
                background: 'white', borderRadius: '14px', padding: '20px 24px',
                border: '1px solid #e2e8f0',
                borderLeft: `4px solid ${colors.text}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '6px' }}>
                      <h4 style={{ fontWeight: 800, color: '#0f172a', margin: 0, fontSize: '1rem' }}>{req.subject}</h4>
                      <span style={{ background: colors.bg, color: colors.text, padding: '3px 8px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 700 }}>
                        {req.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                      To: <strong>{req.requested_to_name}</strong> •
                      Proposed: <strong>{req.proposed_date}</strong> •
                      Type: <strong>{req.meeting_type.replace('_', ' ').toLowerCase()}</strong>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '6px' }}>
                      Requested on {new Date(req.created_at).toLocaleDateString()}
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
