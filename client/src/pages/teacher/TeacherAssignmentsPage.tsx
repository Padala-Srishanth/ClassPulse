import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileText,
  Filter,
  Plus,
  RefreshCw,
  Save,
  Trash2,
  Users,
  X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { classesApi } from '../../api/classes';
import { apiFetch } from '../../api/client';

interface Assignment {
  id: string;
  school_id: string;
  class_id: string;
  teacher_id: string;
  teacher_name: string;
  title: string;
  subject: string;
  description: string;
  due_date: string;
  due_time: string;
  max_marks: number;
  attachments: Array<{ title: string; url: string; file_type?: string }>;
  status: string;
  total_students: number;
  submitted_count: number;
  graded_count: number;
  late_count: number;
  created_at: string;
}

interface SubmissionItem {
  student_id: string;
  student_name: string;
  student_code: string;
  submission_id?: string;
  status: string; // "NOT_SUBMITTED" | "SUBMITTED" | "LATE" | "GRADED"
  submitted_at?: string;
  is_late: boolean;
  content?: string;
  attachment_name?: string;
  attachment_url?: string;
  obtained_marks?: number;
  feedback?: string;
}

interface ClassData {
  id: string;
  name: string;
  grade: string;
  section: string;
}

export const TeacherAssignmentsPage: React.FC = () => {
  const { token, currentUser } = useAuth();
  const [classes, setClasses] = useState<ClassData[]>([]);
  const [selectedClass, setSelectedClass] = useState<string>('');
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);

  // Form state
  const [newTitle, setNewTitle] = useState('');
  const [newSubject, setNewSubject] = useState('Mathematics');
  const [newDueDate, setNewDueDate] = useState('');
  const [newDueTime, setNewDueTime] = useState('23:59');
  const [newMaxMarks, setNewMaxMarks] = useState('20');
  const [newDescription, setNewDescription] = useState('');
  const [newAttachmentTitle, setNewAttachmentTitle] = useState('');
  const [newAttachmentUrl, setNewAttachmentUrl] = useState('');

  // Submissions review drawer/modal
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [roster, setRoster] = useState<SubmissionItem[]>([]);
  const [loadingRoster, setLoadingRoster] = useState(false);
  const [gradingState, setGradingState] = useState<Record<string, { marks: string; feedback: string }>>({});
  const [savingGradeFor, setSavingGradeFor] = useState<string | null>(null);
  const [gradeSuccessFor, setGradeSuccessFor] = useState<string | null>(null);

  // Load teacher classes
  useEffect(() => {
    classesApi.listSchoolClasses(currentUser?.school_id || 'school-001')
      .then((clsList: any) => {
        setClasses(clsList);
        if (clsList.length > 0) setSelectedClass(clsList[0].id);
      })
      .catch(() => {});
  }, [currentUser?.school_id]);

  // Load assignments when class changes
  const loadAssignments = async () => {
    if (!selectedClass) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`/api/v1/assignments?class_id=${selectedClass}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) {
        setAssignments(json.data);
      } else {
        setError(json.error?.message || 'Failed to load assignments');
      }
    } catch (e: any) {
      setError(e.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssignments();
  }, [selectedClass, token]);

  // Open review submissions
  const handleOpenReview = async (assign: Assignment) => {
    setSelectedAssignment(assign);
    setLoadingRoster(true);
    try {
      const res = await apiFetch(`/api/v1/assignments/${assign.id}/submissions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) {
        setRoster(json.data);
        const initialGrading: Record<string, { marks: string; feedback: string }> = {};
        json.data.forEach((s: SubmissionItem) => {
          initialGrading[s.student_id] = {
            marks: s.obtained_marks !== null && s.obtained_marks !== undefined ? String(s.obtained_marks) : '',
            feedback: s.feedback || '',
          };
        });
        setGradingState(initialGrading);
      }
    } catch {
      // ignore
    } finally {
      setLoadingRoster(false);
    }
  };

  // Save grade
  const handleSaveGrade = async (studentId: string) => {
    if (!selectedAssignment) return;
    const gradeInfo = gradingState[studentId];
    if (!gradeInfo || gradeInfo.marks === '') return;

    const numMarks = parseFloat(gradeInfo.marks);
    if (isNaN(numMarks) || numMarks < 0 || numMarks > selectedAssignment.max_marks) {
      alert(`Marks must be between 0 and ${selectedAssignment.max_marks}`);
      return;
    }

    setSavingGradeFor(studentId);
    try {
      const res = await apiFetch(`/api/v1/assignments/${selectedAssignment.id}/submissions/${studentId}/grade`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          obtained_marks: numMarks,
          feedback: gradeInfo.feedback,
        }),
      });
      const json = await res.json();
      if (json.success) {
        setGradeSuccessFor(studentId);
        setTimeout(() => setGradeSuccessFor(null), 2000);
        // Refresh roster
        setRoster(prev => prev.map(s => s.student_id === studentId ? {
          ...s,
          status: 'GRADED',
          obtained_marks: numMarks,
          feedback: gradeInfo.feedback,
        } : s));
        // Refresh assignments metrics
        loadAssignments();
      } else {
        alert(json.error?.message || 'Failed to save grade');
      }
    } catch (e: any) {
      alert(e.message || 'Network error');
    } finally {
      setSavingGradeFor(null);
    }
  };

  // Create assignment
  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClass || !newTitle.trim() || !newDueDate) return;

    setCreating(true);
    try {
      const attachments = [];
      if (newAttachmentTitle.trim() && newAttachmentUrl.trim()) {
        attachments.push({
          title: newAttachmentTitle.trim(),
          url: newAttachmentUrl.trim(),
          file_type: 'pdf',
        });
      }

      const res = await apiFetch('/api/v1/assignments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          class_id: selectedClass,
          title: newTitle.trim(),
          subject: newSubject,
          description: newDescription.trim(),
          due_date: newDueDate,
          due_time: newDueTime || '23:59',
          max_marks: parseFloat(newMaxMarks) || 20,
          attachments,
        }),
      });

      const json = await res.json();
      if (json.success) {
        setShowCreateModal(false);
        setNewTitle('');
        setNewDescription('');
        setNewAttachmentTitle('');
        setNewAttachmentUrl('');
        loadAssignments();
      } else {
        alert(json.error?.message || 'Failed to create assignment');
      }
    } catch (e: any) {
      alert(e.message || 'Network error');
    } finally {
      setCreating(false);
    }
  };

  // Delete assignment
  const handleDelete = async (assignId: string) => {
    if (!window.confirm('Are you sure you want to delete this assignment?')) return;
    try {
      await apiFetch(`/api/v1/assignments/${assignId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      setAssignments(prev => prev.filter(a => a.id !== assignId));
    } catch {
      alert('Failed to delete assignment');
    }
  };

  // Quick stats
  const totalAssignments = assignments.length;
  const totalSubmissions = assignments.reduce((acc, a) => acc + a.submitted_count, 0);
  const totalGraded = assignments.reduce((acc, a) => acc + a.graded_count, 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%)',
        borderRadius: '20px', padding: '28px 32px', color: 'white', position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', top: '-30px', right: '-30px', width: '160px', height: '160px', borderRadius: '50%', background: 'rgba(255,255,255,0.06)' }} />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.8, fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <FileText size={16} /> Classwork & Academic Assignments
            </div>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 900, margin: '6px 0 0', letterSpacing: '-0.02em' }}>
              Assignments Management
            </h1>
            <p style={{ opacity: 0.75, fontSize: '0.88rem', margin: '4px 0 0' }}>
              Create classwork, track student turn-ins, and publish evaluations.
            </p>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: '#4f46e5', color: 'white', border: 'none',
              padding: '12px 20px', borderRadius: '12px', fontWeight: 700,
              fontSize: '0.9rem', cursor: 'pointer', boxShadow: '0 4px 14px rgba(79,70,229,0.4)',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = '#4338ca')}
            onMouseLeave={e => (e.currentTarget.style.background = '#4f46e5')}
          >
            <Plus size={18} /> Create Assignment
          </button>
        </div>
      </div>

      {/* Class Selector & Quick Stats */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'white', padding: '10px 16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <Filter size={16} color="#64748b" />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#64748b' }}>Class:</span>
            <select
              value={selectedClass}
              onChange={e => setSelectedClass(e.target.value)}
              style={{
                border: 'none', outline: 'none', background: 'transparent',
                fontWeight: 700, color: '#0f172a', fontSize: '0.9rem', cursor: 'pointer',
              }}
            >
              {classes.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {[
            { label: 'Assignments', val: totalAssignments, bg: '#eef2ff', col: '#4f46e5' },
            { label: 'Submissions', val: totalSubmissions, bg: '#f0fdf4', col: '#16a34a' },
            { label: 'Graded', val: totalGraded, bg: '#fef3c7', col: '#d97706' },
          ].map(stat => (
            <div key={stat.label} style={{
              background: 'white', border: '1px solid #e2e8f0', borderRadius: '12px',
              padding: '8px 18px', display: 'flex', alignItems: 'center', gap: '10px',
            }}>
              <div style={{
                background: stat.bg, color: stat.col, fontWeight: 800,
                fontSize: '1.1rem', borderRadius: '8px', padding: '2px 10px',
              }}>
                {stat.val}
              </div>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>{stat.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Error notification */}
      {error && (
        <div style={{ padding: '14px 18px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '12px', color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Assignments List */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#64748b', gap: '10px', alignItems: 'center' }}>
          <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite' }} /> Loading assignments...
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : assignments.length === 0 ? (
        <div style={{
          background: 'white', borderRadius: '16px', border: '1px dashed #cbd5e1',
          padding: '48px 24px', textAlign: 'center', color: '#64748b',
        }}>
          <FileText size={40} color="#94a3b8" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', margin: '0 0 6px' }}>
            No assignments created for this class
          </h3>
          <p style={{ fontSize: '0.88rem', margin: '0 0 16px', opacity: 0.8 }}>
            Get started by creating your first homework problem set or essay task.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              background: '#4f46e5', color: 'white', border: 'none',
              padding: '10px 18px', borderRadius: '10px', fontWeight: 600,
              fontSize: '0.88rem', cursor: 'pointer',
            }}
          >
            Create First Assignment
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>
          {assignments.map(a => {
            const subRate = a.total_students > 0 ? Math.round((a.submitted_count / a.total_students) * 100) : 0;
            return (
              <div
                key={a.id}
                style={{
                  background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0',
                  padding: '22px', display: 'flex', flexDirection: 'column', gap: '16px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                  transition: 'transform 0.15s, box-shadow 0.15s',
                }}
              >
                {/* Header info */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                  <div>
                    <span style={{
                      background: '#e0e7ff', color: '#4338ca', fontSize: '0.72rem',
                      fontWeight: 800, padding: '3px 8px', borderRadius: '6px', textTransform: 'uppercase',
                    }}>
                      {a.subject}
                    </span>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: '8px 0 4px', lineHeight: 1.3 }}>
                      {a.title}
                    </h3>
                  </div>
                  <button
                    onClick={() => handleDelete(a.id)}
                    style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
                    title="Delete assignment"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>

                {/* Description */}
                {a.description && (
                  <p style={{ fontSize: '0.84rem', color: '#475569', margin: 0, lineHeight: 1.4, opacity: 0.9 }}>
                    {a.description.length > 110 ? `${a.description.slice(0, 110)}...` : a.description}
                  </p>
                )}

                {/* Due Date & Max marks */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem', color: '#64748b' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Calendar size={14} color="#6366f1" />
                    <span>Due: <strong>{a.due_date}</strong> {a.due_time}</span>
                  </div>
                  <div style={{ fontWeight: 700, color: '#0f172a' }}>
                    Max: {a.max_marks} pts
                  </div>
                </div>

                {/* Progress bar */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 700, marginBottom: '6px' }}>
                    <span style={{ color: '#0f172a' }}>{a.submitted_count} / {a.total_students} Turned In ({subRate}%)</span>
                    <span style={{ color: '#16a34a' }}>{a.graded_count} Graded</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: '#f1f5f9', borderRadius: '999px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${subRate}%`, height: '100%',
                      background: 'linear-gradient(90deg, #4f46e5 0%, #10b981 100%)',
                      borderRadius: '999px',
                    }} />
                  </div>
                </div>

                {/* Review button */}
                <button
                  onClick={() => handleOpenReview(a)}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                    width: '100%', padding: '11px', borderRadius: '10px',
                    background: '#f8fafc', border: '1px solid #cbd5e1',
                    fontWeight: 700, fontSize: '0.85rem', color: '#1e293b', cursor: 'pointer',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#eef2ff')}
                  onMouseLeave={e => (e.currentTarget.style.background = '#f8fafc')}
                >
                  <Users size={16} color="#4f46e5" /> Review & Grade Submissions
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Assignment Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.65)',
          backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '16px',
        }}>
          <div style={{
            background: 'white', borderRadius: '20px', width: '100%', maxWidth: '540px',
            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)', overflow: 'hidden',
          }}>
            <div style={{
              padding: '20px 24px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Plus size={20} color="#4f46e5" /> New Assignment
              </h3>
              <button onClick={() => setShowCreateModal(false)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#64748b' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateAssignment} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Assignment Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Chapter 4 Problem Set"
                  value={newTitle}
                  onChange={e => setNewTitle(e.target.value)}
                  style={{
                    width: '100%', padding: '10px 14px', borderRadius: '10px',
                    border: '1px solid #cbd5e1', fontSize: '0.9rem', outline: 'none',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                    Subject *
                  </label>
                  <select
                    value={newSubject}
                    onChange={e => setNewSubject(e.target.value)}
                    style={{
                      width: '100%', padding: '10px 12px', borderRadius: '10px',
                      border: '1px solid #cbd5e1', fontSize: '0.88rem', background: 'white',
                    }}
                  >
                    {['Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 'Computer Science', 'Social Studies', 'Hindi'].map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                    Max Marks *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="500"
                    required
                    value={newMaxMarks}
                    onChange={e => setNewMaxMarks(e.target.value)}
                    style={{
                      width: '100%', padding: '10px 14px', borderRadius: '10px',
                      border: '1px solid #cbd5e1', fontSize: '0.9rem', outline: 'none',
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                    Due Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={newDueDate}
                    onChange={e => setNewDueDate(e.target.value)}
                    style={{
                      width: '100%', padding: '10px 14px', borderRadius: '10px',
                      border: '1px solid #cbd5e1', fontSize: '0.9rem', outline: 'none',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                    Due Time
                  </label>
                  <input
                    type="time"
                    value={newDueTime}
                    onChange={e => setNewDueTime(e.target.value)}
                    style={{
                      width: '100%', padding: '10px 14px', borderRadius: '10px',
                      border: '1px solid #cbd5e1', fontSize: '0.9rem', outline: 'none',
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Instructions & Guidelines
                </label>
                <textarea
                  rows={3}
                  placeholder="Detail instructions for questions to solve, formatting guidelines..."
                  value={newDescription}
                  onChange={e => setNewDescription(e.target.value)}
                  style={{
                    width: '100%', padding: '10px 14px', borderRadius: '10px',
                    border: '1px solid #cbd5e1', fontSize: '0.88rem', outline: 'none',
                    resize: 'vertical',
                  }}
                />
              </div>

              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569', display: 'block', marginBottom: '8px' }}>
                  Resource / Attachment (Optional)
                </span>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <input
                    type="text"
                    placeholder="Attachment Title (e.g. worksheet.pdf)"
                    value={newAttachmentTitle}
                    onChange={e => setNewAttachmentTitle(e.target.value)}
                    style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.8rem' }}
                  />
                  <input
                    type="text"
                    placeholder="URL (e.g. https://...)"
                    value={newAttachmentUrl}
                    onChange={e => setNewAttachmentUrl(e.target.value)}
                    style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.8rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  style={{
                    padding: '10px 18px', borderRadius: '10px', border: '1px solid #cbd5e1',
                    background: 'white', color: '#475569', fontWeight: 600, fontSize: '0.88rem', cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  style={{
                    padding: '10px 22px', borderRadius: '10px', border: 'none',
                    background: '#4f46e5', color: 'white', fontWeight: 700, fontSize: '0.88rem',
                    cursor: creating ? 'not-allowed' : 'pointer', opacity: creating ? 0.7 : 1,
                  }}
                >
                  {creating ? 'Publishing...' : 'Publish Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Submissions & Grading Drawer Modal */}
      {selectedAssignment && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.65)',
          backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '16px',
        }}>
          <div style={{
            background: 'white', borderRadius: '20px', width: '100%', maxWidth: '850px', maxHeight: '90vh',
            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)', display: 'flex', flexDirection: 'column',
          }}>
            {/* Drawer Header */}
            <div style={{
              padding: '20px 28px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div>
                <span style={{ background: '#e0e7ff', color: '#4338ca', fontSize: '0.72rem', fontWeight: 800, padding: '2px 8px', borderRadius: '6px' }}>
                  {selectedAssignment.subject}
                </span>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 900, color: '#0f172a', margin: '4px 0 2px' }}>
                  {selectedAssignment.title}
                </h2>
                <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                  Max Marks: <strong>{selectedAssignment.max_marks}</strong> • Due: {selectedAssignment.due_date} {selectedAssignment.due_time}
                </span>
              </div>
              <button
                onClick={() => setSelectedAssignment(null)}
                style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={22} />
              </button>
            </div>

            {/* Submissions Roster */}
            <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
              {loadingRoster ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '40px', color: '#64748b', gap: '8px' }}>
                  <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite' }} /> Loading submissions...
                </div>
              ) : roster.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#64748b' }}>No students found in this class.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {roster.map(item => {
                    const isGraded = item.status === 'GRADED';
                    const isLate = item.is_late;
                    const isSubmitted = item.status === 'SUBMITTED' || isGraded || isLate;
                    const isSaving = savingGradeFor === item.student_id;
                    const isSuccess = gradeSuccessFor === item.student_id;

                    return (
                      <div
                        key={item.student_id}
                        style={{
                          border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px 20px',
                          background: isGraded ? '#fcfdfe' : isSubmitted ? '#fff' : '#f8fafc',
                          display: 'flex', flexDirection: 'column', gap: '10px',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                          <div>
                            <div style={{ fontWeight: 800, color: '#0f172a', fontSize: '0.95rem' }}>
                              {item.student_name}
                              <span style={{ marginLeft: '8px', color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>
                                ({item.student_code})
                              </span>
                            </div>
                            {item.submitted_at && (
                              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                                Turned in: {new Date(item.submitted_at).toLocaleDateString()} at {new Date(item.submitted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            )}
                          </div>

                          {/* Status Badge */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {isGraded ? (
                              <span style={{ background: '#dcfce7', color: '#15803d', fontSize: '0.75rem', fontWeight: 800, padding: '3px 10px', borderRadius: '999px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <CheckCircle2 size={13} /> Graded: {item.obtained_marks}/{selectedAssignment.max_marks}
                              </span>
                            ) : isLate ? (
                              <span style={{ background: '#fee2e2', color: '#b91c1c', fontSize: '0.75rem', fontWeight: 800, padding: '3px 10px', borderRadius: '999px' }}>
                                Late Submission
                              </span>
                            ) : isSubmitted ? (
                              <span style={{ background: '#e0f2fe', color: '#0369a1', fontSize: '0.75rem', fontWeight: 800, padding: '3px 10px', borderRadius: '999px' }}>
                                Submitted
                              </span>
                            ) : (
                              <span style={{ background: '#f1f5f9', color: '#64748b', fontSize: '0.75rem', fontWeight: 800, padding: '3px 10px', borderRadius: '999px' }}>
                                Not Submitted
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Student content / notes / attachment */}
                        {item.content && (
                          <div style={{ background: '#f8fafc', padding: '8px 12px', borderRadius: '8px', fontSize: '0.82rem', color: '#334155' }}>
                            <strong>Student Note:</strong> {item.content}
                          </div>
                        )}
                        {item.attachment_name && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#4f46e5' }}>
                            <FileText size={14} />
                            <a
                              href={item.attachment_url || '#'}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: '#4f46e5', textDecoration: 'underline', fontWeight: 600 }}
                            >
                              {item.attachment_name}
                            </a>
                            <ExternalLink size={12} />
                          </div>
                        )}

                        {/* Grading Inputs */}
                        <div style={{
                          display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap',
                          paddingTop: '8px', borderTop: '1px dashed #e2e8f0', marginTop: '4px',
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569' }}>Marks:</label>
                            <input
                              type="number"
                              min="0"
                              max={selectedAssignment.max_marks}
                              step="0.5"
                              placeholder={`0 - ${selectedAssignment.max_marks}`}
                              value={gradingState[item.student_id]?.marks ?? ''}
                              onChange={e => setGradingState(prev => ({
                                ...prev,
                                [item.student_id]: { ...prev[item.student_id], marks: e.target.value },
                              }))}
                              style={{
                                width: '70px', padding: '6px 8px', borderRadius: '8px',
                                border: '1px solid #cbd5e1', fontSize: '0.85rem', fontWeight: 700,
                              }}
                            />
                            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>/ {selectedAssignment.max_marks}</span>
                          </div>

                          <div style={{ flex: 1, minWidth: '200px' }}>
                            <input
                              type="text"
                              placeholder="Feedback comment (e.g. Great work, check step 3)..."
                              value={gradingState[item.student_id]?.feedback ?? ''}
                              onChange={e => setGradingState(prev => ({
                                ...prev,
                                [item.student_id]: { ...prev[item.student_id], feedback: e.target.value },
                              }))}
                              style={{
                                width: '100%', padding: '6px 10px', borderRadius: '8px',
                                border: '1px solid #cbd5e1', fontSize: '0.82rem',
                              }}
                            />
                          </div>

                          <button
                            onClick={() => handleSaveGrade(item.student_id)}
                            disabled={isSaving}
                            style={{
                              display: 'flex', alignItems: 'center', gap: '6px',
                              padding: '6px 14px', borderRadius: '8px', border: 'none',
                              background: isSuccess ? '#16a34a' : '#4f46e5', color: 'white',
                              fontWeight: 700, fontSize: '0.8rem', cursor: isSaving ? 'not-allowed' : 'pointer',
                              transition: 'background 0.2s',
                            }}
                          >
                            {isSuccess ? <CheckCircle2 size={14} /> : <Save size={14} />}
                            {isSuccess ? 'Saved!' : isSaving ? 'Saving...' : 'Save Grade'}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
