import React, { useState, useEffect } from 'react';
import { AlertCircle, Calendar, Check, CheckCheck, Clock, Save, UserCheck, X } from 'lucide-react';
import { classesApi } from '../api/classes';
import { Student } from '../types';

interface TakeAttendanceModalProps {
  classId: string;
  className: string;
  students: Student[];
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const TakeAttendanceModal: React.FC<TakeAttendanceModalProps> = ({
  classId,
  className,
  students,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const todayStr = new Date().toISOString().split('T')[0];
  const [date, setDate] = useState(todayStr);
  const [attendanceMap, setAttendanceMap] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Default all students to PRESENT when opened
  useEffect(() => {
    if (isOpen && students.length > 0) {
      const initial: Record<string, string> = {};
      students.forEach((s) => {
        initial[s.id] = attendanceMap[s.id] || 'PRESENT';
      });
      setAttendanceMap(initial);
    }
  }, [isOpen, students]);

  if (!isOpen) return null;

  const markAll = (status: string) => {
    const updated: Record<string, string> = {};
    students.forEach((s) => {
      updated[s.id] = status;
    });
    setAttendanceMap(updated);
  };

  const handleStatusChange = (studentId: string, status: string) => {
    setAttendanceMap((prev) => ({
      ...prev,
      [studentId]: status,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!date) {
      setError('Please select a valid date for attendance.');
      return;
    }

    setSubmitting(true);
    setError(null);

    const records = students.map((s) => ({
      student_id: s.id,
      status: attendanceMap[s.id] || 'PRESENT',
    }));

    try {
      await classesApi.recordClassAttendance(classId, date, records);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to submit class attendance.');
    } finally {
      setSubmitting(false);
    }
  };

  const presentCount = Object.values(attendanceMap).filter((s) => s === 'PRESENT').length;
  const absentCount = Object.values(attendanceMap).filter((s) => s === 'ABSENT').length;
  const lateCount = Object.values(attendanceMap).filter((s) => s === 'LATE').length;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: '680px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Class Attendance Sheet</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Class: <strong>{className}</strong> • Total Enrolled: <strong>{students.length}</strong>
            </p>
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

            {/* Controls Bar: Date & Quick Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', background: '#f8fafc', padding: '12px 16px', borderRadius: '10px', marginBottom: '18px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Calendar size={16} color="#4f46e5" />
                <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>Date:</label>
                <input
                  type="date"
                  className="form-input"
                  style={{ padding: '4px 8px', fontSize: '0.82rem', width: '140px' }}
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={() => markAll('PRESENT')}
                >
                  <CheckCheck size={14} color="#16a34a" />
                  Mark All Present
                </button>
              </div>
            </div>

            {/* Live Count Status */}
            <div style={{ display: 'flex', gap: '16px', fontSize: '0.82rem', marginBottom: '16px', padding: '0 4px' }}>
              <span style={{ color: '#15803d', fontWeight: 600 }}>🟢 Present: {presentCount}</span>
              <span style={{ color: '#b91c1c', fontWeight: 600 }}>🔴 Absent: {absentCount}</span>
              {lateCount > 0 && <span style={{ color: '#b45309', fontWeight: 600 }}>🟡 Late: {lateCount}</span>}
            </div>

            {/* Student Roster Table */}
            <div style={{ maxHeight: '360px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '10px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead style={{ position: 'sticky', top: 0, background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', zIndex: 2 }}>
                  <tr>
                    <th style={{ padding: '10px 14px', fontSize: '0.75rem', color: '#64748b' }}>Roll ID</th>
                    <th style={{ padding: '10px 14px', fontSize: '0.75rem', color: '#64748b' }}>Student Name</th>
                    <th style={{ padding: '10px 14px', fontSize: '0.75rem', color: '#64748b', textAlign: 'right' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((stu) => {
                    const currentStatus = attendanceMap[stu.id] || 'PRESENT';

                    return (
                      <tr key={stu.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '10px 14px', fontSize: '0.82rem', fontWeight: 600, color: '#475569' }}>
                          {stu.student_code}
                        </td>
                        <td style={{ padding: '10px 14px', fontSize: '0.88rem', fontWeight: 600, color: '#0f172a' }}>
                          {stu.name}
                        </td>
                        <td style={{ padding: '8px 14px', textAlign: 'right' }}>
                          <div style={{ display: 'inline-flex', gap: '4px', background: '#f1f5f9', padding: '3px', borderRadius: '8px' }}>
                            {[
                              { id: 'PRESENT', label: 'Present', activeBg: '#16a34a' },
                              { id: 'ABSENT', label: 'Absent', activeBg: '#dc2626' },
                              { id: 'LATE', label: 'Late', activeBg: '#d97706' },
                            ].map((btn) => {
                              const isActive = currentStatus === btn.id;
                              return (
                                <button
                                  key={btn.id}
                                  type="button"
                                  onClick={() => handleStatusChange(stu.id, btn.id)}
                                  style={{
                                    border: 'none',
                                    borderRadius: '6px',
                                    padding: '4px 10px',
                                    fontSize: '0.75rem',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    background: isActive ? btn.activeBg : 'transparent',
                                    color: isActive ? 'white' : '#64748b',
                                    transition: 'all 0.1s ease',
                                  }}
                                >
                                  {btn.label}
                                </button>
                              );
                            })}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              <Save size={16} />
              {submitting ? 'Saving Attendance...' : 'Submit Attendance Sheet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
