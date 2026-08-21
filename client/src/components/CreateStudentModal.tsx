import React, { useState } from 'react';
import { AlertCircle, GraduationCap, Phone, UserPlus, X } from 'lucide-react';
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
  const [name, setName] = useState('');
  const [studentCode, setStudentCode] = useState('');
  const [classId, setClassId] = useState(defaultClassId || (classes[0]?.id || ''));
  const [section, setSection] = useState(classes[0]?.section || 'A');
  const [parentContact, setParentContact] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const currentClass = classes.find((c) => c.id === classId);
  const grade = currentClass ? currentClass.grade : '10';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !studentCode.trim()) {
      setError('Please provide both Full Name and Roll Number.');
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
        section: section.trim().toUpperCase(),
        parent_contact: parentContact.trim() || undefined,
        status: 'ACTIVE',
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to enroll student');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: '560px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Enroll New Student</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Fill in student information and parent contact</p>
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

            {/* 1. Full Name */}
            <div className="form-group">
              <label className="form-label">Full Name *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Aarav Sharma"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            {/* 2. Roll Number */}
            <div className="form-group">
              <label className="form-label">Roll Number / Student Code *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. ROLL-101 / DPS-106"
                value={studentCode}
                onChange={(e) => setStudentCode(e.target.value)}
                required
              />
            </div>

            {/* 3. Class & 4. Section */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Class *</label>
                <select
                  className="form-select"
                  value={classId}
                  onChange={(e) => {
                    setClassId(e.target.value);
                    const sel = classes.find((c) => c.id === e.target.value);
                    if (sel) {
                      setSection(sel.section);
                    }
                  }}
                >
                  {classes.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} (Grade {c.grade})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Section *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. A"
                  value={section}
                  onChange={(e) => setSection(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* 5. Parent's Contact */}
            <div className="form-group">
              <label className="form-label">Parent's Contact (Phone / Email)</label>
              <div style={{ position: 'relative' }}>
                <Phone size={15} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                <input
                  type="text"
                  className="form-input"
                  style={{ paddingLeft: '36px' }}
                  placeholder="+91 98765 43210 / parent@gmail.com"
                  value={parentContact}
                  onChange={(e) => setParentContact(e.target.value)}
                />
              </div>
            </div>

            {/* 6. Note on Exam-based Grading */}
            <div style={{ background: '#f8fafc', padding: '12px 14px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.8rem', color: '#475569', display: 'flex', gap: '10px', alignItems: 'center' }}>
              <GraduationCap size={20} color="#4f46e5" style={{ flexShrink: 0 }} />
              <div>
                <strong>Academic Grading Note:</strong> Performance grades (A+, A, B, C, D, F) are automatically calculated and updated continuously from individual exam scores & test results.
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              <UserPlus size={16} />
              {submitting ? 'Enrolling...' : 'Enroll Student'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
