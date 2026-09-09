import React, { useEffect, useState } from 'react';
import {
  BookOpen, CalendarDays, Check, Clock, Edit2, Plus, RefreshCw, Trash2, X, AlertCircle,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../api/client';
import { classesApi } from '../../api/classes';
import { SchoolClass } from '../../types';

const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const DAY_LABELS: Record<string, string> = {
  MON: 'Monday', TUE: 'Tuesday', WED: 'Wednesday',
  THU: 'Thursday', FRI: 'Friday', SAT: 'Saturday',
};

interface TimetableSlot {
  id: string;
  class_id: string;
  day_of_week: string;
  period_number: number;
  subject: string;
  teacher_id: string;
  teacher_name: string;
  start_time: string;
  end_time: string;
}

interface SlotForm {
  day_of_week: string;
  period_number: number;
  subject: string;
  teacher_id: string;
  teacher_name: string;
  start_time: string;
  end_time: string;
}

const emptyForm = (): SlotForm => ({
  day_of_week: 'MON',
  period_number: 1,
  subject: '',
  teacher_id: '',
  teacher_name: '',
  start_time: '09:00',
  end_time: '09:50',
});

export const TimetableManagementPage: React.FC = () => {
  const { token, schoolId } = useAuth();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<string>('');
  const [selectedDay, setSelectedDay] = useState<string>('MON');
  const [slots, setSlots] = useState<TimetableSlot[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingSlot, setEditingSlot] = useState<TimetableSlot | null>(null);
  const [form, setForm] = useState<SlotForm>(emptyForm());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!schoolId) return;
    classesApi.listSchoolClasses(schoolId).then(setClasses).catch(console.error);
  }, [schoolId]);

  const loadSlots = async (classId: string) => {
    if (!classId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`/api/v1/timetables/class/${classId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) setSlots(json.data);
      else setError(json.error?.message || 'Failed to load timetable');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedClassId) loadSlots(selectedClassId);
    else setSlots([]);
  }, [selectedClassId]);

  const daySlots = slots.filter(s => s.day_of_week === selectedDay)
    .sort((a, b) => a.period_number - b.period_number);

  const openCreate = () => {
    setEditingSlot(null);
    setForm({ ...emptyForm(), day_of_week: selectedDay });
    setShowForm(true);
    setError(null);
  };

  const openEdit = (slot: TimetableSlot) => {
    setEditingSlot(slot);
    setForm({
      day_of_week: slot.day_of_week,
      period_number: slot.period_number,
      subject: slot.subject,
      teacher_id: slot.teacher_id,
      teacher_name: slot.teacher_name,
      start_time: slot.start_time,
      end_time: slot.end_time,
    });
    setShowForm(true);
    setError(null);
  };

  const handleSave = async () => {
    if (!selectedClassId || !schoolId) return;
    setSaving(true);
    setError(null);
    try {
      let res: Response;
      if (editingSlot) {
        res = await apiFetch(`/api/v1/timetables/${editingSlot.id}`, {
          method: 'PATCH',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify(form),
        });
      } else {
        res = await apiFetch('/api/v1/timetables', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...form, class_id: selectedClassId, school_id: schoolId }),
        });
      }
      const json = await res.json();
      if (json.success) {
        setShowForm(false);
        setSuccessMsg(editingSlot ? 'Slot updated!' : 'Slot added!');
        setTimeout(() => setSuccessMsg(null), 2500);
        await loadSlots(selectedClassId);
      } else {
        setError(json.error?.message || 'Save failed');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (slot: TimetableSlot) => {
    if (!window.confirm(`Delete ${slot.subject} (Period ${slot.period_number}) on ${DAY_LABELS[slot.day_of_week]}?`)) return;
    try {
      const res = await apiFetch(`/api/v1/timetables/${slot.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.success) {
        setSuccessMsg('Slot deleted!');
        setTimeout(() => setSuccessMsg(null), 2000);
        await loadSlots(selectedClassId);
      } else {
        setError(json.error?.message || 'Delete failed');
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', boxSizing: 'border-box',
    padding: '10px 14px', borderRadius: '10px',
    border: '1.5px solid #e2e8f0', fontSize: '0.875rem',
    outline: 'none', background: 'white', color: '#0f172a',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #064e3b 0%, #065f46 100%)',
        borderRadius: '20px', padding: '28px 32px', color: 'white',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <CalendarDays size={22} color="#6ee7b7" />
          <span style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', opacity: 0.8 }}>Timetable Management</span>
        </div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 900, margin: 0 }}>Class Timetable</h1>
        <p style={{ opacity: 0.75, margin: '6px 0 0', fontSize: '0.9rem' }}>Set weekly schedules for each class</p>
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

      {/* Class Selector */}
      <div style={{ background: 'white', borderRadius: '16px', padding: '20px', border: '1px solid #e2e8f0' }}>
        <label style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.85rem', display: 'block', marginBottom: '8px' }}>Select Class</label>
        <select
          value={selectedClassId}
          onChange={e => setSelectedClassId(e.target.value)}
          style={{ ...inputStyle, cursor: 'pointer' }}
        >
          <option value="">-- Choose a class --</option>
          {classes.map(cls => (
            <option key={cls.id} value={cls.id}>{cls.name || `Grade ${cls.grade}-${cls.section}`}</option>
          ))}
        </select>
      </div>

      {/* Timetable editor */}
      {selectedClassId && (
        <div style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          {/* Day Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', background: '#f8fafc', overflowX: 'auto' }}>
            {DAYS.map(day => (
              <button
                key={day}
                onClick={() => { setSelectedDay(day); setShowForm(false); }}
                style={{
                  flex: '0 0 auto', padding: '14px 20px', border: 'none',
                  borderBottom: selectedDay === day ? '3px solid #059669' : '3px solid transparent',
                  background: 'transparent', cursor: 'pointer',
                  color: selectedDay === day ? '#059669' : '#64748b',
                  fontWeight: selectedDay === day ? 700 : 500, fontSize: '0.85rem',
                  whiteSpace: 'nowrap', transition: 'all 0.15s',
                }}
              >
                {DAY_LABELS[day].slice(0, 3)}
              </button>
            ))}
          </div>

          <div style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.95rem' }}>{DAY_LABELS[selectedDay]}</div>
              <button
                onClick={openCreate}
                style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  background: '#064e3b', color: 'white',
                  padding: '8px 16px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                  fontWeight: 700, fontSize: '0.82rem',
                }}
              >
                <Plus size={15} /> Add Period
              </button>
            </div>

            {/* Slot Form */}
            {showForm && (
              <div style={{
                background: '#f8fafc', borderRadius: '14px', padding: '20px',
                border: '1.5px solid #e2e8f0', marginBottom: '16px',
              }}>
                <div style={{ fontWeight: 700, color: '#0f172a', marginBottom: '16px', fontSize: '0.9rem' }}>
                  {editingSlot ? 'Edit Period' : 'Add New Period'}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Day</label>
                    <select style={inputStyle} value={form.day_of_week} onChange={e => setForm(f => ({ ...f, day_of_week: e.target.value }))}>
                      {DAYS.map(d => <option key={d} value={d}>{DAY_LABELS[d]}</option>)}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Period #</label>
                    <input type="number" min={1} max={12} style={inputStyle} value={form.period_number}
                      onChange={e => setForm(f => ({ ...f, period_number: parseInt(e.target.value) || 1 }))} />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Subject</label>
                    <input style={inputStyle} placeholder="e.g. Mathematics" value={form.subject}
                      onChange={e => setForm(f => ({ ...f, subject: e.target.value }))} />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Teacher Name</label>
                    <input style={inputStyle} placeholder="Full name" value={form.teacher_name}
                      onChange={e => setForm(f => ({ ...f, teacher_name: e.target.value }))} />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '4px' }}>Teacher ID / UID</label>
                    <input style={inputStyle} placeholder="teacher-uid-..." value={form.teacher_id}
                      onChange={e => setForm(f => ({ ...f, teacher_id: e.target.value }))} />
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
                </div>
                <div style={{ display: 'flex', gap: '10px', marginTop: '16px', justifyContent: 'flex-end' }}>
                  <button
                    onClick={() => setShowForm(false)}
                    style={{ padding: '8px 18px', borderRadius: '10px', border: '1.5px solid #e2e8f0', background: 'white', cursor: 'pointer', fontWeight: 600, fontSize: '0.82rem', color: '#64748b' }}
                  >Cancel</button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    style={{ padding: '8px 18px', borderRadius: '10px', border: 'none', background: '#064e3b', color: 'white', cursor: 'pointer', fontWeight: 700, fontSize: '0.82rem', opacity: saving ? 0.7 : 1 }}
                  >{saving ? 'Saving...' : (editingSlot ? 'Update' : 'Add Period')}</button>
                </div>
              </div>
            )}

            {/* Period List */}
            {loading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '36px', gap: '12px' }}>
                <RefreshCw size={20} color="#059669" style={{ animation: 'spin 1s linear infinite' }} />
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                <span style={{ color: '#64748b' }}>Loading...</span>
              </div>
            ) : daySlots.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '36px', color: '#94a3b8' }}>
                <CalendarDays size={40} style={{ marginBottom: '10px', opacity: 0.4 }} />
                <p style={{ fontWeight: 600 }}>No periods on {DAY_LABELS[selectedDay]}</p>
                <p style={{ fontSize: '0.82rem', marginTop: '4px' }}>Click "Add Period" to create one.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {daySlots.map(slot => (
                  <div key={slot.id} style={{
                    display: 'flex', alignItems: 'center', gap: '14px',
                    padding: '14px 18px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0',
                  }}>
                    <div style={{
                      width: '40px', height: '40px', borderRadius: '10px', background: '#dcfce7',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontWeight: 800, color: '#16a34a', fontSize: '0.9rem', flexShrink: 0,
                    }}>
                      {slot.period_number}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.9rem' }}>{slot.subject}</div>
                      <div style={{ color: '#64748b', fontSize: '0.75rem' }}>{slot.teacher_name}</div>
                    </div>
                    <div style={{ fontWeight: 700, color: '#059669', fontSize: '0.82rem', whiteSpace: 'nowrap' }}>
                      {slot.start_time} – {slot.end_time}
                    </div>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        onClick={() => openEdit(slot)}
                        style={{ padding: '6px', borderRadius: '8px', border: 'none', background: '#e0f2fe', cursor: 'pointer' }}
                        title="Edit"
                      ><Edit2 size={14} color="#0891b2" /></button>
                      <button
                        onClick={() => handleDelete(slot)}
                        style={{ padding: '6px', borderRadius: '8px', border: 'none', background: '#fef2f2', cursor: 'pointer' }}
                        title="Delete"
                      ><Trash2 size={14} color="#ef4444" /></button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
