import React, { useState } from 'react';
import { X, Send, AlertTriangle } from 'lucide-react';
import { InterventionType } from '../types';
import { interventionsApi } from '../api/interventions';

interface InterventionModalProps {
  studentId: string;
  studentName: string;
  schoolId: string;
  classId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const InterventionModal: React.FC<InterventionModalProps> = ({
  studentId,
  studentName,
  schoolId,
  classId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [type, setType] = useState<InterventionType>('ACADEMIC_SUPPORT');
  const [notes, setNotes] = useState('');
  const [followUpDate, setFollowUpDate] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim()) {
      setError('Please provide detailed action notes for this intervention.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await interventionsApi.createIntervention({
        student_id: studentId,
        school_id: schoolId,
        class_id: classId,
        type,
        notes: notes.trim(),
        follow_up_date: followUpDate || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to record intervention');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Create Intervention Action Plan</h3>
            <p style={{ fontSize: '0.8rem', color: '#64748b' }}>For student: <strong>{studentName}</strong></p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
              <div style={{ background: '#fef2f2', border: '1px solid #fecdd3', color: '#b91c1c', padding: '10px 14px', borderRadius: '8px', marginBottom: '16px', fontSize: '0.85rem', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <AlertTriangle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Intervention Category</label>
              <select
                className="form-select"
                value={type}
                onChange={(e) => setType(e.target.value as InterventionType)}
              >
                <option value="ACADEMIC_SUPPORT">Academic Remedial / Tutoring</option>
                <option value="PARENT_CONTACT">Parent Outreach & Consultation</option>
                <option value="COUNSELING_REFERRAL">Student Counselor Referral</option>
                <option value="EXTRA_ASSIGNMENT">Targeted Practice Work</option>
                <option value="ONE_ON_ONE_SUPPORT">1-on-1 Teacher Check-in</option>
                <option value="OTHER">Other Structured Action</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Scheduled Follow-up Date</label>
              <input
                type="date"
                className="form-input"
                value={followUpDate}
                onChange={(e) => setFollowUpDate(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Action Notes & Strategy</label>
              <textarea
                className="form-textarea"
                rows={4}
                placeholder="Describe the root cause discussion, agreed plan, and expectations for the student..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              <Send size={16} />
              {submitting ? 'Saving Action...' : 'Record Intervention'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
