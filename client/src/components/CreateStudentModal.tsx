import React, { useState } from 'react';
import { AlertCircle, UserPlus, X } from 'lucide-react';
import { studentsApi } from '../api/students';
import { SchoolClass } from '../types';

interface CreateStudentModalProps {
  schoolId: string;
  classes: SchoolClass[];
  defaultClassId?: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateStudentModal: React.FC<CreateStudentModalProps> = ({
  schoolId,
  classes,
  defaultClassId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [studentCode, setStudentCode] = useState('');
  const [name, setName] = useState('');
  const [classId, setClassId] = useState(defaultClassId || (classes[0]?.id || ''));
  const [grade, setGrade] = useState('10');
  const [section, setSection] = useState('A');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentCode.trim() || !name.trim()) {
      setError('Please provide both Student Code and Student Name.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await studentsApi.createStudent({
        school_id: schoolId,
        class_id: classId,
        student_code: studentCode.trim().toUpperCase(),
        name: name.trim(),
        grade,
        section,
        status: 'ACTIVE',
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create student');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Enroll New Student</h3>
            <p style={{ fontSize: '0.8rem', color: '#64748b' }}>Add a student to school records</p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
              <div style={{ background: '#fef2f2', border: '1px solid #fecdd3', color: '#b91c1c', padding: '10px 14px', borderRadius: '8px', marginBottom: '16px', fontSize: '0.85rem', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Student ID / Roll Code</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. DPS-106"
                value={studentCode}
                onChange={(e) => setStudentCode(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Neha Gupta"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Assign Class</label>
              <select
                className="form-select"
                value={classId}
                onChange={(e) => {
                  setClassId(e.target.value);
                  const sel = classes.find((c) => c.id === e.target.value);
                  if (sel) {
                    setGrade(sel.grade);
                    setSection(sel.section);
                  }
                }}
              >
                {classes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} (Grade {c.grade}-{c.section})
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Grade</label>
                <input
                  type="text"
                  className="form-input"
                  value={grade}
                  onChange={(e) => setGrade(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Section</label>
                <input
                  type="text"
                  className="form-input"
                  value={section}
                  onChange={(e) => setSection(e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              <UserPlus size={16} />
              {submitting ? 'Creating...' : 'Enroll Student'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
