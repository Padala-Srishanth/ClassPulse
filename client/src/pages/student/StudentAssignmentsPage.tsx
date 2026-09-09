import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Award,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileText,
  Paperclip,
  RefreshCw,
  Send,
  Upload,
  X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../api/client';

interface AssignmentItem {
  assignment: {
    id: string;
    school_id: string;
    class_id: string;
    teacher_name: string;
    title: string;
    subject: string;
    description: string;
    due_date: string;
    due_time: string;
    max_marks: number;
    attachments: Array<{ title: string; url: string; file_type?: string }>;
    status: string;
  };
  submission?: {
    id: string;
    submitted_at?: string;
    content?: string;
    attachment_name?: string;
    attachment_url?: string;
    status: string;
    is_late: boolean;
    obtained_marks?: number;
    feedback?: string;
  };
  urgency: string; // "DUE_TODAY" | "DUE_TOMORROW" | "THIS_WEEK" | "UPCOMING" | "OVERDUE" | "COMPLETED"
  days_remaining: number;
  is_submitted: boolean;
  is_graded: boolean;
}

export const StudentAssignmentsPage: React.FC = () => {
  const { token } = useAuth();
  const [items, setItems] = useState<AssignmentItem[]>([]);
  const [activeTab, setActiveTab] = useState<'pending' | 'completed' | 'overdue' | 'all'>('pending');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Turn in modal
  const [selectedItem, setSelectedItem] = useState<AssignmentItem | null>(null);
  const [submitContent, setSubmitContent] = useState('');
  const [submitAttachmentName, setSubmitAttachmentName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadAssignments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch('/api/v1/student/assignments', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) {
        setItems(json.data.all || []);
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
  }, [token]);

  // Handle turn in
  const handleSubmitWork = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem) return;

    setSubmitting(true);
    try {
      const res = await apiFetch(`/api/v1/student/assignments/${selectedItem.assignment.id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          content: submitContent.trim() || 'Submitted via student portal',
          attachment_name: submitAttachmentName.trim() || 'homework_solution.pdf',
          attachment_url: 'https://example.com/homework_solution.pdf',
        }),
      });
      const json = await res.json();
      if (json.success) {
        setSelectedItem(null);
        setSubmitContent('');
        setSubmitAttachmentName('');
        loadAssignments();
      } else {
        alert(json.error?.message || 'Submission failed');
      }
    } catch (e: any) {
      alert(e.message || 'Network error');
    } finally {
      setSubmitting(false);
    }
  };

  // Filter items
  const pendingItems = items.filter(i => !i.is_submitted && i.urgency !== 'OVERDUE');
  const completedItems = items.filter(i => i.is_submitted);
  const overdueItems = items.filter(i => !i.is_submitted && i.urgency === 'OVERDUE');

  const displayedItems =
    activeTab === 'pending'
      ? pendingItems
      : activeTab === 'completed'
      ? completedItems
      : activeTab === 'overdue'
      ? overdueItems
      : items;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #0c4a6e 0%, #0284c7 50%, #0891b2 100%)',
        borderRadius: '20px', padding: '28px 32px', color: 'white', position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', top: '-30px', right: '-30px', width: '160px', height: '160px', borderRadius: '50%', background: 'rgba(255,255,255,0.06)' }} />
        <div style={{ position: 'relative' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.85, fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <FileText size={16} /> Student Classwork
          </div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 900, margin: '6px 0 0', letterSpacing: '-0.02em' }}>
            My Assignments
          </h1>
          <p style={{ opacity: 0.8, fontSize: '0.88rem', margin: '4px 0 0' }}>
            View homework deadlines, download class resources, and turn in your responses.
          </p>
        </div>
      </div>

      {/* Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
        {[
          { label: 'Assigned', count: items.length, col: '#0891b2', bg: '#e0f2fe' },
          { label: 'Pending', count: pendingItems.length, col: '#d97706', bg: '#fef3c7' },
          { label: 'Completed', count: completedItems.length, col: '#16a34a', bg: '#dcfce7' },
          { label: 'Overdue', count: overdueItems.length, col: '#dc2626', bg: '#fee2e2' },
        ].map(card => (
          <div key={card.label} style={{
            background: 'white', borderRadius: '14px', padding: '14px 18px', border: '1px solid #e2e8f0',
            display: 'flex', alignItems: 'center', gap: '14px',
          }}>
            <div style={{
              width: '40px', height: '40px', borderRadius: '10px', background: card.bg,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900,
              color: card.col, fontSize: '1.2rem', flexShrink: 0,
            }}>
              {card.count}
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                {card.label}
              </div>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0f172a' }}>
                {card.count} {card.count === 1 ? 'task' : 'tasks'}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #e2e8f0', paddingBottom: '10px', flexWrap: 'wrap' }}>
        {[
          { id: 'pending', label: `Due Soon (${pendingItems.length})`, count: pendingItems.length },
          { id: 'overdue', label: `Overdue (${overdueItems.length})`, count: overdueItems.length },
          { id: 'completed', label: `Completed (${completedItems.length})`, count: completedItems.length },
          { id: 'all', label: `All (${items.length})`, count: items.length },
        ].map(tab => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: '8px 16px', borderRadius: '999px', border: 'none',
                background: isActive ? '#0891b2' : '#f1f5f9',
                color: isActive ? 'white' : '#475569',
                fontWeight: 700, fontSize: '0.84rem', cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Error state */}
      {error && (
        <div style={{ padding: '14px 18px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '12px', color: '#b91c1c' }}>
          {error}
        </div>
      )}

      {/* Assignments List */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#64748b', gap: '8px' }}>
          <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite' }} /> Loading assignments...
        </div>
      ) : displayedItems.length === 0 ? (
        <div style={{
          background: 'white', borderRadius: '16px', border: '1px dashed #cbd5e1',
          padding: '48px 24px', textAlign: 'center', color: '#64748b',
        }}>
          <CheckCircle2 size={40} color="#10b981" style={{ margin: '0 auto 12px', opacity: 0.8 }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', margin: '0 0 4px' }}>
            {activeTab === 'pending' ? 'All caught up!' : 'No assignments found'}
          </h3>
          <p style={{ fontSize: '0.85rem', margin: 0, opacity: 0.8 }}>
            {activeTab === 'pending' ? 'You have no pending assignments due.' : 'Check back later for newly published classwork.'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {displayedItems.map(item => {
            const a = item.assignment;
            const sub = item.submission;
            const isGraded = item.is_graded;
            const isSubmitted = item.is_submitted;
            const isOverdue = item.urgency === 'OVERDUE';

            // Urgency styling
            let urgencyBadge = { bg: '#e0f2fe', col: '#0369a1', label: `${item.days_remaining}d left` };
            if (isGraded) {
              urgencyBadge = { bg: '#dcfce7', col: '#15803d', label: 'Graded' };
            } else if (isSubmitted) {
              urgencyBadge = { bg: '#e0e7ff', col: '#4338ca', label: sub?.is_late ? 'Turned In Late' : 'Turned In' };
            } else if (isOverdue) {
              urgencyBadge = { bg: '#fee2e2', col: '#b91c1c', label: 'Overdue' };
            } else if (item.urgency === 'DUE_TODAY') {
              urgencyBadge = { bg: '#fee2e2', col: '#dc2626', label: 'Due Today' };
            } else if (item.urgency === 'DUE_TOMORROW') {
              urgencyBadge = { bg: '#fff7ed', col: '#ea580c', label: 'Due Tomorrow' };
            }

            return (
              <div
                key={a.id}
                style={{
                  background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0',
                  padding: '22px', display: 'flex', flexDirection: 'column', gap: '14px',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{
                        background: '#e0f2fe', color: '#0369a1', fontSize: '0.72rem',
                        fontWeight: 800, padding: '3px 8px', borderRadius: '6px', textTransform: 'uppercase',
                      }}>
                        {a.subject}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>• Assigned by {a.teacher_name}</span>
                    </div>
                    <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                      {a.title}
                    </h3>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      background: urgencyBadge.bg, color: urgencyBadge.col,
                      fontSize: '0.75rem', fontWeight: 800, padding: '4px 10px', borderRadius: '999px',
                    }}>
                      {urgencyBadge.label}
                    </span>
                  </div>
                </div>

                {/* Description */}
                {a.description && (
                  <p style={{ fontSize: '0.88rem', color: '#334155', margin: 0, lineHeight: 1.5 }}>
                    {a.description}
                  </p>
                )}

                {/* Attachments from teacher */}
                {a.attachments && a.attachments.length > 0 && (
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {a.attachments.map((att, idx) => (
                      <a
                        key={idx}
                        href={att.url}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          display: 'inline-flex', alignItems: 'center', gap: '6px',
                          padding: '6px 12px', background: '#f8fafc', border: '1px solid #e2e8f0',
                          borderRadius: '8px', fontSize: '0.8rem', color: '#0284c7', fontWeight: 600,
                          textDecoration: 'none',
                        }}
                      >
                        <Paperclip size={13} /> {att.title}
                      </a>
                    ))}
                  </div>
                )}

                {/* Submission or Grading Card */}
                {isGraded ? (
                  <div style={{
                    background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '12px',
                    padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: '8px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#166534', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Award size={16} color="#16a34a" /> Graded by Teacher
                      </span>
                      <span style={{ fontWeight: 900, fontSize: '1.1rem', color: '#15803d' }}>
                        {sub?.obtained_marks} / {a.max_marks} pts ({Math.round(((sub?.obtained_marks || 0) / a.max_marks) * 100)}%)
                      </span>
                    </div>
                    {sub?.feedback && (
                      <p style={{ fontSize: '0.84rem', color: '#14532d', margin: 0, fontStyle: 'italic' }}>
                        "{sub.feedback}"
                      </p>
                    )}
                  </div>
                ) : isSubmitted ? (
                  <div style={{
                    background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px',
                    padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <CheckCircle2 size={16} color="#0891b2" />
                      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                        Work submitted on {sub?.submitted_at ? new Date(sub.submitted_at).toLocaleDateString() : 'recently'}. Awaiting teacher evaluation.
                      </span>
                    </div>
                    {sub?.attachment_name && (
                      <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
                        Attached: {sub.attachment_name}
                      </span>
                    )}
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', paddingTop: '6px' }}>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Clock size={14} /> Deadline: <strong>{a.due_date}</strong> at {a.due_time} ({a.max_marks} pts)
                    </div>

                    <button
                      onClick={() => {
                        setSelectedItem(item);
                        setSubmitContent('');
                        setSubmitAttachmentName('');
                      }}
                      style={{
                        display: 'inline-flex', alignItems: 'center', gap: '6px',
                        background: isOverdue ? '#dc2626' : '#0891b2', color: 'white',
                        border: 'none', padding: '9px 18px', borderRadius: '10px',
                        fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer',
                        transition: 'opacity 0.15s',
                      }}
                    >
                      <Upload size={14} /> Turn In Work
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Turn In Work Modal */}
      {selectedItem && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.65)',
          backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '16px',
        }}>
          <div style={{
            background: 'white', borderRadius: '20px', width: '100%', maxWidth: '520px',
            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)', overflow: 'hidden',
          }}>
            <div style={{
              padding: '20px 24px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#0369a1', textTransform: 'uppercase' }}>
                  {selectedItem.assignment.subject}
                </span>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', margin: '2px 0 0' }}>
                  Turn In: {selectedItem.assignment.title}
                </h3>
              </div>
              <button onClick={() => setSelectedItem(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#64748b' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmitWork} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {selectedItem.urgency === 'OVERDUE' && (
                <div style={{
                  padding: '10px 14px', background: '#fef2f2', border: '1px solid #fecaca',
                  borderRadius: '10px', fontSize: '0.82rem', color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '8px',
                }}>
                  <AlertCircle size={16} />
                  <span>The deadline for this assignment has passed. Your submission will be marked <strong>LATE</strong>.</span>
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Your Response / Working Notes
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="Type your answer, solution explanations, or notes for your teacher..."
                  value={submitContent}
                  onChange={e => setSubmitContent(e.target.value)}
                  style={{
                    width: '100%', padding: '10px 14px', borderRadius: '10px',
                    border: '1px solid #cbd5e1', fontSize: '0.88rem', outline: 'none',
                    resize: 'vertical',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Attachment File Name / Document
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type="text"
                    placeholder="e.g. math_ch4_answers.pdf"
                    value={submitAttachmentName}
                    onChange={e => setSubmitAttachmentName(e.target.value)}
                    style={{
                      flex: 1, padding: '10px 14px', borderRadius: '10px',
                      border: '1px solid #cbd5e1', fontSize: '0.88rem', outline: 'none',
                    }}
                  />
                  <div style={{
                    padding: '10px 14px', background: '#f1f5f9', borderRadius: '10px',
                    fontSize: '0.8rem', fontWeight: 700, color: '#475569', display: 'flex', alignItems: 'center', gap: '4px',
                  }}>
                    <Upload size={14} /> Attached
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => setSelectedItem(null)}
                  style={{
                    padding: '10px 18px', borderRadius: '10px', border: '1px solid #cbd5e1',
                    background: 'white', color: '#475569', fontWeight: 600, fontSize: '0.88rem', cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '6px',
                    padding: '10px 22px', borderRadius: '10px', border: 'none',
                    background: '#0891b2', color: 'white', fontWeight: 700, fontSize: '0.88rem',
                    cursor: submitting ? 'not-allowed' : 'pointer', opacity: submitting ? 0.7 : 1,
                  }}
                >
                  <Send size={15} /> {submitting ? 'Submitting...' : 'Turn In Work'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
