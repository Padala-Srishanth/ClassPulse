import React, { useEffect, useState } from 'react';
import { Calendar, CheckCircle2, MessageCircle, RefreshCw, XCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface MeetingRequest {
  id: string;
  meeting_type: string;
  subject: string;
  message: string;
  status: string;
  requested_by_name: string;
  proposed_date: string;
  proposed_time?: string;
  created_at: string;
  response_note?: string;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  PENDING: { bg: '#fffbeb', text: '#d97706' },
  ACCEPTED: { bg: '#f0fdf4', text: '#16a34a' },
  DECLINED: { bg: '#fef2f2', text: '#ef4444' },
  COMPLETED: { bg: '#eef2ff', text: '#4f46e5' },
  CANCELLED: { bg: '#f8fafc', text: '#64748b' },
};

export const TeacherMessagesPage: React.FC = () => {
  const { token, currentUser } = useAuth();
  const [requests, setRequests] = useState<MeetingRequest[]>([]);
  const [loading, setLoading] = useState(true);

  const loadRequests = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/student/meeting-requests', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) {
        setRequests(json.data || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0f172a', marginBottom: '4px' }}>
          Student Appointments & Messages
        </h1>
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
          Review and manage meeting requests from your students.
        </p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#64748b' }}>
          <RefreshCw size={28} color="#4f46e5" style={{ animation: 'spin 1s linear infinite' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <p style={{ marginTop: '12px' }}>Loading appointment requests...</p>
        </div>
      ) : requests.length === 0 ? (
        <div style={{ background: 'white', borderRadius: '16px', padding: '60px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
          <MessageCircle size={40} color="#d1d5db" style={{ marginBottom: '16px' }} />
          <h3 style={{ color: '#0f172a', margin: '0 0 8px 0' }}>No Pending Requests</h3>
          <p style={{ color: '#64748b', margin: 0 }}>You have no appointment requests scheduled from students at this time.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {requests.map((req) => {
            const colors = STATUS_COLORS[req.status] || { bg: '#f8fafc', text: '#64748b' };
            return (
              <div
                key={req.id}
                style={{
                  background: 'white',
                  borderRadius: '14px',
                  padding: '20px 24px',
                  border: '1px solid #e2e8f0',
                  borderLeft: `4px solid ${colors.text}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '6px' }}>
                      <h4 style={{ fontWeight: 800, color: '#0f172a', margin: 0, fontSize: '1rem' }}>{req.subject}</h4>
                      <span style={{ background: colors.bg, color: colors.text, padding: '3px 8px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 700 }}>
                        {req.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '6px' }}>
                      From: <strong>{req.requested_by_name}</strong> • Proposed Date: <strong>{req.proposed_date}</strong>
                    </div>
                    {req.message && (
                      <p style={{ color: '#334155', fontSize: '0.875rem', margin: '0 0 8px 0', background: '#f8fafc', padding: '10px 14px', borderRadius: '8px' }}>
                        "{req.message}"
                      </p>
                    )}
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
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
