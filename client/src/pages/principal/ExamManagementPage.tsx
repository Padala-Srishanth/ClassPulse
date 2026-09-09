import React, { useEffect, useState } from 'react';
import {
  BookOpen, CalendarDays, Check, GraduationCap, Plus, RefreshCw, AlertCircle,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../api/client';
import { classesApi } from '../../api/classes';
import { SchoolClass } from '../../types';

interface ExamEntry {
  id: string;
  class_id: string;
  exam_name: string;
  subject: string;
  exam_date: string;
  max_marks: number;
  status: string;
  start_time?: string;
  end_time?: string;
  description?: string;
}

interface ExamForm {
  class_id: string;
  exam_name: string;
  subject: string;
  exam_date: string;
  max_marks: number;
  start_time: string;
  end_time: string;
  description: string;
}

const emptyForm = (): ExamForm => ({
  class_id: '',
  exam_name: '',
  subject: '',
  exam_date: '',
  max_marks: 100,
  start_time: '',
  end_time: '',
  description: '',
});

const STATUS_STYLES: Record<string, { bg: string; color: string }> = {
  UPCOMING:  { bg: '#eff6ff', color: '#2563eb' },
  ONGOING:   { bg: '#fef9c3', color: '#a16207' },
  COMPLETED: { bg: '#f0fdf4', color: '#16a34a' },
  CANCELLED: { bg: '#fef2f2', color: '#dc2626' },
};

export const ExamManagementPage: React.FC = () => {
  const { token, schoolId } = useAuth();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [filterClassId, setFilterClassId] = useState('');
  const [exams, setExams] = useState<ExamEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<ExamForm>(emptyForm());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!schoolId) return;
    classesApi.listSchoolClasses(schoolId).then(setClasses).catch(console.error);
  }, [schoolId]);

  const loadExams = async (classId: string) => {
    if (!classId) { setExams([]); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`/api/v1/exams/class/${classId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) setExams(json.data);
      else setError(json.error?.message || 'Failed to load exams');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExams(filterClassId);
  }, [filterClassId]);

  const handleSave = async () => {
    if (!form.class_id || !form.exam_name || !form.subject || !form.exam_date || !schoolId) {
      setError('Please fill in all required fields.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const body: any = {
        school_id: schoolId,
        class_id: form.class_id,
        exam_name: form.exam_name,
        subject: form.subject,
        exam_date: form.exam_date,
        max_marks: form.max_marks,
      };
      if (form.start_time) body.start_time = form.start_time;
      if (form.end_time) body.end_time = form.end_time;
      if (form.description) body.description = form.description;

      const res = await apiFetch('/api/v1/exams', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      if (json.success) {
        setShowForm(false);
        setForm(emptyForm());
        setSuccessMsg('Exam created successfully!');
        setTimeout(() => setSuccessMsg(null), 2500);
        if (filterClassId === form.class_id) await loadExams(filterClassId);
        else setFilterClassId(form.class_id);
      } else {
        setError(json.error?.message || 'Failed to create exam');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', boxSizing: 'border-box',
    padding: '10px 14px', borderRadius: '10px',
    border: '1.5px solid #e2e8f0', fontSize: '0.875rem',
    outline: 'none', background: 'white', color: '#0f172a',
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #064e3b 0%, #065f46 100%)',
        borderRadius: '20px', padding: '28px 32px', color: 'white',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <GraduationCap size={22} color="#6ee7b7" />
          <span style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', opacity: 0.8 }}>Exam Management</span>
        </div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 900, margin: 0 }}>School Exams</h1>
        <p style={{ opacity: 0.75, margin: '6px 0 0', fontSize: '0.9rem' }}>Create and manage exam schedules for all classes</p>
      </div>

      {/* Alerts */}
      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '12px', padding: '14px 18px', display: 'flex', gap: '10px', alignItems: 'center' }}>
          <AlertCircle size={18} color="#ef4444" /><span style={{ color: '#dc2626', fontSize: '0.875rem' }}>{error}</span>
        </div>
      )}
      {successMsg && (
        <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '12px', padding: '14px 18px', display: 'flex', gap: '10px', alignItems: 'center' }}>
          <Check size={18} color="#16a34a" /><span style={{ color: '#16a34a', fontSize: '0.875rem' }}>{successMsg}</span>
        </div>
      )}

      {/* Controls */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
        <select
          value={filterClassId}
          onChange={e => setFilterClassId(e.target.value)}
          style={{ ...inputStyle, maxWidth: '300px' }}
        >
          <option value="">-- Filter by class --</option>
          {classes.map(cls => (
            <option key={cls.id} value={cls.id}>{cls.name || `Grade ${cls.grade}-${cls.section}`}</option>
          ))}
        </select>
        <button
          onClick={() => { setShowForm(!showForm); setError(null); }}
          style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            background: '#064e3b', color: 'white', padding: '10px 20px',
            borderRadius: '12px', border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: '0.875rem',
            whiteSpace: 'nowrap',
          }}
        >
          <Plus size={16} /> Create Exam
        </button>
      </div>

      {/* Create Exam Form */}
      {showForm && (
        <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '20px', fontSize: '1rem' }}>New Exam</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Class *</label>
              <select style={inputStyle} value={form.class_id} onChange={e => setForm(f => ({ ...f, class_id: e.target.value }))}>
                <option value="">-- Select class --</option>
                {classes.map(cls => <option key={cls.id} value={cls.id}>{cls.name || `Grade ${cls.grade}-${cls.section}`}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Exam Name *</label>
              <input style={inputStyle} placeholder="e.g. Mid-Term Exam" value={form.exam_name}
                onChange={e => setForm(f => ({ ...f, exam_name: e.target.value }))} />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Subject *</label>
              <input style={inputStyle} placeholder="e.g. Mathematics" value={form.subject}
                onChange={e => setForm(f => ({ ...f, subject: e.target.value }))} />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Exam Date *</label>
              <input type="date" style={inputStyle} min={today} value={form.exam_date}
                onChange={e => setForm(f => ({ ...f, exam_date: e.target.value }))} />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Max Marks *</label>
              <input type="number" min={1} style={inputStyle} value={form.max_marks}
                onChange={e => setForm(f => ({ ...f, max_marks: parseFloat(e.target.value) || 100 }))} />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Start Time</label>
              <input type="time" style={inputStyle} value={form.start_time}
                onChange={e => setForm(f => ({ ...f, start_time: e.target.value }))} />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>End Time</label>
              <input type="time" style={inputStyle} value={form.end_time}
                onChange={e => setForm(f => ({ ...f, end_time: e.target.value }))} />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Description / Notes</label>
              <textarea rows={2} style={{ ...inputStyle, resize: 'vertical' }} placeholder="e.g. Covers chapters 1-5"
                value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px', marginTop: '18px', justifyContent: 'flex-end' }}>
            <button onClick={() => setShowForm(false)} style={{ padding: '10px 20px', borderRadius: '10px', border: '1.5px solid #e2e8f0', background: 'white', cursor: 'pointer', fontWeight: 600, color: '#64748b', fontSize: '0.875rem' }}>Cancel</button>
            <button onClick={handleSave} disabled={saving} style={{ padding: '10px 20px', borderRadius: '10px', border: 'none', background: '#064e3b', color: 'white', cursor: 'pointer', fontWeight: 700, fontSize: '0.875rem', opacity: saving ? 0.7 : 1 }}>
              {saving ? 'Creating...' : 'Create Exam'}
            </button>
          </div>
        </div>
      )}

      {/* Exam List */}
      <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
        <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '18px', fontSize: '1rem' }}>
          {filterClassId ? `Exams for ${classes.find(c => c.id === filterClassId)?.name || 'Selected Class'}` : 'Select a class to view exams'}
        </h3>

        {!filterClassId ? (
          <div style={{ textAlign: 'center', padding: '48px', color: '#94a3b8' }}>
            <BookOpen size={48} style={{ marginBottom: '12px', opacity: 0.3 }} />
            <p>Select a class from the dropdown above</p>
          </div>
        ) : loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '36px', gap: '12px' }}>
            <RefreshCw size={20} color="#059669" style={{ animation: 'spin 1s linear infinite' }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            <span style={{ color: '#64748b' }}>Loading exams...</span>
          </div>
        ) : exams.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px', color: '#94a3b8' }}>
            <GraduationCap size={48} style={{ marginBottom: '12px', opacity: 0.3 }} />
            <p>No exams created yet. Click "Create Exam" to add one.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {exams.map(exam => {
              const statusStyle = STATUS_STYLES[exam.status] || STATUS_STYLES.UPCOMING;
              return (
                <div key={exam.id} style={{
                  display: 'flex', alignItems: 'flex-start', gap: '16px',
                  padding: '16px 20px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0',
                }}>
                  <div style={{
                    width: '42px', height: '42px', borderRadius: '12px', background: '#dcfce7',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  }}>
                    <GraduationCap size={20} color="#16a34a" />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.95rem' }}>{exam.exam_name}</div>
                    <div style={{ color: '#64748b', fontSize: '0.78rem', marginTop: '3px' }}>
                      {exam.subject} • {exam.exam_date}
                      {exam.start_time && ` • ${exam.start_time}–${exam.end_time}`}
                      {' '} • Max: {exam.max_marks}
                    </div>
                    {exam.description && (
                      <div style={{ color: '#94a3b8', fontSize: '0.73rem', marginTop: '3px' }}>{exam.description}</div>
                    )}
                  </div>
                  <span style={{
                    background: statusStyle.bg, color: statusStyle.color,
                    padding: '3px 10px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 700, whiteSpace: 'nowrap',
                  }}>{exam.status}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
