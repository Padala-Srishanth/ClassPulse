import React, { useState } from 'react';
import { Calendar, CheckCircle, Clock, Edit3, MessageSquare } from 'lucide-react';
import { Intervention, InterventionOutcome, InterventionStatus } from '../types';
import { interventionsApi } from '../api/interventions';

interface InterventionTimelineProps {
  interventions: Intervention[];
  onRefresh: () => void;
}

export const InterventionTimeline: React.FC<InterventionTimelineProps> = ({
  interventions,
  onRefresh,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [status, setStatus] = useState<InterventionStatus>('IN_PROGRESS');
  const [outcome, setOutcome] = useState<InterventionOutcome>('STUDENT_IMPROVED');
  const [outcomeNotes, setOutcomeNotes] = useState('');
  const [updating, setUpdating] = useState(false);

  if (!interventions || interventions.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8', background: '#f8fafc', borderRadius: '12px' }}>
        No interventions have been recorded for this student yet.
      </div>
    );
  }

  const handleUpdate = async (id: string) => {
    setUpdating(true);
    try {
      await interventionsApi.updateIntervention(id, {
        status,
        outcome: status === 'COMPLETED' ? outcome : undefined,
        outcome_notes: outcomeNotes || undefined,
      });
      setEditingId(null);
      onRefresh();
    } catch (e) {
      alert('Failed to update intervention');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {interventions.map((item) => {
        const isEditing = editingId === item.id;
        const isCompleted = item.status === 'COMPLETED';

        return (
          <div key={item.id} className="card" style={{ padding: '18px 20px', borderLeft: isCompleted ? '4px solid #10b981' : '4px solid #6366f1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <div>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '6px',
                    background: '#f1f5f9',
                    color: '#334155',
                    textTransform: 'uppercase',
                    marginRight: '8px',
                  }}
                >
                  {item.type.replace(/_/g, ' ')}
                </span>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '6px',
                    background: isCompleted ? '#d1fae5' : '#e0e7ff',
                    color: isCompleted ? '#065f46' : '#3730a3',
                    textTransform: 'uppercase',
                  }}
                >
                  {item.status}
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Calendar size={13} />
                {new Date(item.created_at).toLocaleDateString()}
              </span>
            </div>

            <p style={{ fontSize: '0.9rem', color: '#1e293b', margin: '10px 0', lineHeight: 1.4 }}>
              {item.notes}
            </p>

            {item.follow_up_date && (
              <div style={{ fontSize: '0.78rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px' }}>
                <Clock size={13} />
                <span>Follow-up: <strong>{item.follow_up_date}</strong></span>
              </div>
            )}

            {item.outcome && (
              <div style={{ marginTop: '12px', padding: '10px 14px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', fontSize: '0.82rem' }}>
                <div style={{ fontWeight: 600, color: '#166534', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle size={14} />
                  Outcome: {item.outcome.replace(/_/g, ' ')}
                </div>
                {item.outcome_notes && (
                  <p style={{ color: '#14532d', marginTop: '4px', fontSize: '0.8rem' }}>{item.outcome_notes}</p>
                )}
              </div>
            )}

            {!isCompleted && !isEditing && (
              <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => {
                    setEditingId(item.id);
                    setStatus(item.status);
                  }}
                >
                  <Edit3 size={13} />
                  Update Status & Outcome
                </button>
              </div>
            )}

            {isEditing && (
              <div style={{ marginTop: '14px', padding: '14px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                  <div>
                    <label className="form-label">Status</label>
                    <select
                      className="form-select"
                      value={status}
                      onChange={(e) => setStatus(e.target.value as InterventionStatus)}
                    >
                      <option value="PLANNED">PLANNED</option>
                      <option value="IN_PROGRESS">IN PROGRESS</option>
                      <option value="COMPLETED">COMPLETED</option>
                      <option value="CANCELLED">CANCELLED</option>
                    </select>
                  </div>

                  {status === 'COMPLETED' && (
                    <div>
                      <label className="form-label">Observed Outcome</label>
                      <select
                        className="form-select"
                        value={outcome}
                        onChange={(e) => setOutcome(e.target.value as InterventionOutcome)}
                      >
                        <option value="STUDENT_IMPROVED">Student Improved</option>
                        <option value="STUDENT_UNCHANGED">Student Unchanged</option>
                        <option value="STUDENT_DECLINED_FURTHER">Student Declined Further</option>
                        <option value="REFERRED_FOR_ADDITIONAL_SUPPORT">Referred For Additional Support</option>
                        <option value="OTHER">Other</option>
                      </select>
                    </div>
                  )}
                </div>

                <div style={{ marginBottom: '12px' }}>
                  <label className="form-label">Outcome Notes</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Result summary after follow-up..."
                    value={outcomeNotes}
                    onChange={(e) => setOutcomeNotes(e.target.value)}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                  <button className="btn btn-outline btn-sm" onClick={() => setEditingId(null)} disabled={updating}>
                    Cancel
                  </button>
                  <button className="btn btn-primary btn-sm" onClick={() => handleUpdate(item.id)} disabled={updating}>
                    {updating ? 'Saving...' : 'Save Updates'}
                  </button>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
