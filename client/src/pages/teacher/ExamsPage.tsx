import React, { useEffect, useState } from 'react';
import { BookOpen, CheckCircle2, GraduationCap, Plus, RefreshCw, Save, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { classesApi } from '../../api/classes';
import { studentsApi } from '../../api/students';
import { apiFetch } from '../../api/client';

interface Exam {
  id: string; school_id: string; class_id: string; teacher_id: string;
  exam_name: string; subject: string; exam_date: string; max_marks: number; status: string;
}
interface ExamResult {
  id: string; student_id: string; obtained_marks: number; max_marks: number; percentage: number; grade: string;
}
interface ClassData { id: string; name: string; grade: string; section: string; }
interface StudentData { id: string; name: string; student_code: string; }

export const ExamsPage: React.FC = () => {
  const { token } = useAuth();
  const [classes, setClasses] = useState<ClassData[]>([]);
  const [selectedClass, setSelectedClass] = useState<string>('');
  const [exams, setExams] = useState<Exam[]>([]);
  const [students, setStudents] = useState<StudentData[]>([]);
  const [selectedExam, setSelectedExam] = useState<Exam | null>(null);
  const [examResults, setExamResults] = useState<ExamResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateExam, setShowCreateExam] = useState(false);
  const [showEnterMarks, setShowEnterMarks] = useState(false);
  const [saving, setSaving] = useState(false);
  const [marks, setMarks] = useState<Record<string, string>>({});
  const [examForm, setExamForm] = useState({
    exam_name: '', subject: '', exam_date: '', max_marks: '100',
  });

  useEffect(() => {
    classesApi.listSchoolClasses('school-001').then((c: any) => {
      setClasses(c);
      if (c.length > 0) setSelectedClass(c[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedClass) { setExams([]); return; }
    setLoading(true);
    apiFetch(`/api/v1/exams/class/${selectedClass}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(j => { if (j.success) setExams(j.data); })
      .finally(() => setLoading(false));

    studentsApi.listClassStudents(selectedClass).then((s: any) => setStudents(s));
  }, [selectedClass]);

  const loadExamResults = async (examId: string) => {
    const res = await apiFetch(`/api/v1/exams/${examId}/results`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const json = await res.json();
    if (json.success) setExamResults(json.data.results || []);
  };

  const createExam = async () => {
    if (!examForm.exam_name || !examForm.subject || !examForm.exam_date || !selectedClass) return;
    setSaving(true);
    try {
      const res = await apiFetch('/api/v1/exams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          school_id: 'school-001', class_id: selectedClass,
          exam_name: examForm.exam_name, subject: examForm.subject,
          exam_date: examForm.exam_date, max_marks: parseFloat(examForm.max_marks),
        }),
      });
      const json = await res.json();
      if (json.success) {
        setExams(prev => [...prev, json.data]);
        setShowCreateExam(false);
        setExamForm({ exam_name: '', subject: '', exam_date: '', max_marks: '100' });
      }
    } finally { setSaving(false); }
  };

  const submitMarks = async () => {
    if (!selectedExam) return;
    setSaving(true);
    try {
      const results = students
        .filter(s => marks[s.id] !== undefined && marks[s.id] !== '')
        .map(s => ({ student_id: s.id, obtained_marks: parseFloat(marks[s.id]) }));
      const res = await apiFetch(`/api/v1/exams/${selectedExam.id}/results`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ results }),
      });
      const json = await res.json();
      if (json.success) {
        alert(`✅ Saved ${json.data.saved.length} results. ${json.data.errors.length > 0 ? `${json.data.errors.length} errors.` : ''}`);
        setShowEnterMarks(false);
        setMarks({});
        loadExamResults(selectedExam.id);
      }
    } finally { setSaving(false); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0f172a', marginBottom: '4px' }}>Exams & Marks</h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Create exams, enter marks for students, and view class performance.</p>
        </div>
      </div>

      {/* Class selector */}
      <div style={{ background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0', display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Select Class</label>
          <select
            value={selectedClass} onChange={e => { setSelectedClass(e.target.value); setSelectedExam(null); setShowEnterMarks(false); }}
            style={{ width: '100%', padding: '10px 14px', border: '1.5px solid #e2e8f0', borderRadius: '10px', fontSize: '0.9rem', outline: 'none', background: 'white' }}
          >
            <option value="">Choose a class...</option>
            {classes.map(c => <option key={c.id} value={c.id}>{c.name} (Grade {c.grade}-{c.section})</option>)}
          </select>
        </div>
        {selectedClass && (
          <button onClick={() => setShowCreateExam(true)} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 18px', background: '#4f46e5', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 700 }}>
            <Plus size={16} /> New Exam
          </button>
        )}
      </div>

      {/* Create Exam Form */}
      {showCreateExam && (
        <div style={{ background: 'white', borderRadius: '16px', padding: '28px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BookOpen size={18} color="#4f46e5" /> Create New Exam
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px' }}>
            {[
              { key: 'exam_name', label: 'Exam Name', placeholder: 'e.g. Mid-Term Math' },
              { key: 'subject', label: 'Subject', placeholder: 'e.g. Mathematics' },
              { key: 'exam_date', label: 'Date', placeholder: '', type: 'date' },
              { key: 'max_marks', label: 'Max Marks', placeholder: '100', type: 'number' },
            ].map(({ key, label, placeholder, type = 'text' }) => (
              <div key={key}>
                <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>{label}</label>
                <input
                  type={type} value={(examForm as any)[key]} placeholder={placeholder}
                  onChange={e => setExamForm({ ...examForm, [key]: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', border: '1.5px solid #e2e8f0', borderRadius: '10px', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box' }}
                />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button onClick={() => setShowCreateExam(false)} style={{ padding: '10px 20px', background: '#f1f5f9', color: '#475569', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 600 }}>Cancel</button>
            <button onClick={createExam} disabled={saving} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', background: '#4f46e5', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 700 }}>
              <CheckCircle2 size={16} /> {saving ? 'Creating...' : 'Create Exam'}
            </button>
          </div>
        </div>
      )}

      {/* Exams List */}
      {selectedClass && (
        <div style={{ background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GraduationCap size={18} color="#4f46e5" /> Exams ({exams.length})
          </h3>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              <RefreshCw size={24} color="#4f46e5" style={{ animation: 'spin 1s linear infinite' }} />
              <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
          ) : exams.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>No exams created yet. Click "New Exam" to create one.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {exams.map(exam => (
                <div key={exam.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '14px 18px', background: selectedExam?.id === exam.id ? '#eef2ff' : '#f8fafc',
                  borderRadius: '12px', border: selectedExam?.id === exam.id ? '1.5px solid #6366f1' : '1px solid #e2e8f0',
                  gap: '12px', flexWrap: 'wrap',
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>{exam.exam_name}</div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
                      {exam.subject} • {exam.exam_date} • Max: {exam.max_marks} marks
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={async () => { setSelectedExam(exam); setShowEnterMarks(false); await loadExamResults(exam.id); }}
                      style={{ padding: '7px 14px', background: '#eef2ff', color: '#4f46e5', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.8rem' }}
                    >
                      View Results
                    </button>
                    <button
                      onClick={() => { setSelectedExam(exam); setShowEnterMarks(true); setMarks({}); }}
                      style={{ padding: '7px 14px', background: '#4f46e5', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.8rem' }}
                    >
                      Enter Marks
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Enter Marks Panel */}
      {showEnterMarks && selectedExam && (
        <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Enter Marks — {selectedExam.exam_name} (Max: {selectedExam.max_marks})
            </h3>
            <button onClick={() => setShowEnterMarks(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}><X size={20} /></button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
            {students.map(stu => (
              <div key={stu.id} style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '12px 16px', background: '#f8fafc', borderRadius: '10px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.9rem' }}>{stu.name}</div>
                  <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>#{stu.student_code}</div>
                </div>
                <input
                  type="number" min="0" max={selectedExam.max_marks}
                  value={marks[stu.id] || ''}
                  onChange={e => setMarks({ ...marks, [stu.id]: e.target.value })}
                  placeholder={`0 – ${selectedExam.max_marks}`}
                  style={{ width: '120px', padding: '8px 12px', border: '1.5px solid #e2e8f0', borderRadius: '8px', fontSize: '0.9rem', outline: 'none', textAlign: 'right' }}
                />
                {marks[stu.id] && (
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#4f46e5', minWidth: '50px', textAlign: 'right' }}>
                    {((parseFloat(marks[stu.id]) / selectedExam.max_marks) * 100).toFixed(1)}%
                  </span>
                )}
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button onClick={() => setShowEnterMarks(false)} style={{ padding: '10px 20px', background: '#f1f5f9', color: '#475569', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 600 }}>Cancel</button>
            <button onClick={submitMarks} disabled={saving} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', background: '#4f46e5', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 700 }}>
              <Save size={16} /> {saving ? 'Saving...' : 'Save Marks'}
            </button>
          </div>
        </div>
      )}

      {/* Results Panel */}
      {selectedExam && !showEnterMarks && examResults.length > 0 && (
        <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '16px' }}>
            Results — {selectedExam.exam_name}
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {examResults.map(r => {
              const student = students.find(s => s.id === r.student_id);
              return (
                <div key={r.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: '#f8fafc', borderRadius: '10px' }}>
                  <span style={{ fontWeight: 600, color: '#0f172a' }}>{student?.name || r.student_id}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span style={{ color: '#64748b', fontSize: '0.85rem' }}>{r.obtained_marks}/{r.max_marks}</span>
                    <span style={{ fontWeight: 700, color: '#0f172a' }}>{r.percentage.toFixed(1)}%</span>
                    <span style={{
                      background: r.grade === 'F' ? '#fef2f2' : '#f0fdf4',
                      color: r.grade === 'F' ? '#dc2626' : '#16a34a',
                      padding: '3px 10px', borderRadius: '6px', fontWeight: 700, fontSize: '0.82rem',
                    }}>{r.grade}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
