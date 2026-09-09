import React, { useEffect, useState } from 'react';
import {
  BookOpen, CalendarDays, ChevronLeft, ChevronRight, Clock, RefreshCw, AlertCircle,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../api/client';

const DAYS = [
  { key: 'MON', label: 'Monday' },
  { key: 'TUE', label: 'Tuesday' },
  { key: 'WED', label: 'Wednesday' },
  { key: 'THU', label: 'Thursday' },
  { key: 'FRI', label: 'Friday' },
  { key: 'SAT', label: 'Saturday' },
];

const SUBJECT_COLORS: Record<string, { bg: string; color: string }> = {
  Mathematics:  { bg: '#eef2ff', color: '#4f46e5' },
  Science:      { bg: '#f0fdf4', color: '#16a34a' },
  Physics:      { bg: '#f0fdf4', color: '#059669' },
  Chemistry:    { bg: '#fef9c3', color: '#a16207' },
  Biology:      { bg: '#ecfdf5', color: '#10b981' },
  English:      { bg: '#fdf2f8', color: '#a21caf' },
  Hindi:        { bg: '#fff7ed', color: '#ea580c' },
  History:      { bg: '#fef3c7', color: '#d97706' },
  Geography:    { bg: '#ecfeff', color: '#0891b2' },
};

function getSubjectStyle(subject: string) {
  return SUBJECT_COLORS[subject] || { bg: '#eff6ff', color: '#2563eb' };
}

function formatClassName(classId: string): string {
  if (!classId) return '';
  const match = classId.match(/class-(\d+)([a-zA-Z]+)/i);
  if (match) {
    return `Class ${match[1]}-${match[2].toUpperCase()}`;
  }
  return classId;
}

interface TimetableSlot {
  id: string;
  class_id: string;
  day_of_week: string;
  period_number: number;
  subject: string;
  teacher_name: string;
  start_time: string;
  end_time: string;
}

export const TeacherTimetablePage: React.FC = () => {
  const { token } = useAuth();
  const [slots, setSlots] = useState<TimetableSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<string>('MON');

  useEffect(() => {
    const dayMap: Record<number, string> = { 0: 'SAT', 1: 'MON', 2: 'TUE', 3: 'WED', 4: 'THU', 5: 'FRI', 6: 'SAT' };
    setSelectedDay(dayMap[new Date().getDay()] || 'MON');
  }, []);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiFetch('/api/v1/timetables/my', {
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
    load();
  }, [token]);

  const grouped: Record<string, TimetableSlot[]> = {};
  for (const slot of slots) {
    if (!grouped[slot.day_of_week]) grouped[slot.day_of_week] = [];
    grouped[slot.day_of_week].push(slot);
  }
  for (const day of Object.keys(grouped)) {
    grouped[day].sort((a, b) => a.period_number - b.period_number);
  }

  const selectedSlots = grouped[selectedDay] || [];
  const dayIndex = DAYS.findIndex(d => d.key === selectedDay);
  const prevDay = dayIndex > 0 ? DAYS[dayIndex - 1] : null;
  const nextDay = dayIndex < DAYS.length - 1 ? DAYS[dayIndex + 1] : null;

  const totalPeriodsPerWeek = slots.length;
  const todayLabel = DAYS.find(d => d.key === selectedDay)?.label || '';

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px', flexDirection: 'column', gap: '16px' }}>
        <RefreshCw size={32} color="#4f46e5" style={{ animation: 'spin 1s linear infinite' }} />
        <p style={{ color: '#64748b' }}>Loading your schedule...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1e1b4b 0%, #4f46e5 100%)',
        borderRadius: '20px', padding: '28px 32px', color: 'white',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', top: '-40px', right: '-40px', width: '180px', height: '180px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
        <div style={{ position: 'relative' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <CalendarDays size={22} color="#a5b4fc" />
            <span style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', opacity: 0.8 }}>My Teaching Schedule</span>
          </div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 900, margin: 0 }}>My Timetable</h1>
          <p style={{ opacity: 0.75, margin: '6px 0 0', fontSize: '0.9rem' }}>
            {totalPeriodsPerWeek} period{totalPeriodsPerWeek !== 1 ? 's' : ''} per week
          </p>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '12px', padding: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertCircle size={20} color="#ef4444" />
          <span style={{ color: '#dc2626', fontSize: '0.875rem' }}>{error}</span>
        </div>
      )}

      {/* Weekly Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: '10px' }}>
        {DAYS.map(day => {
          const count = (grouped[day.key] || []).length;
          const isToday = day.key === selectedDay;
          return (
            <button
              key={day.key}
              onClick={() => setSelectedDay(day.key)}
              style={{
                padding: '14px 8px', borderRadius: '12px',
                border: isToday ? '2px solid #4f46e5' : '1.5px solid #e2e8f0',
                background: isToday ? '#eef2ff' : 'white',
                cursor: 'pointer', textAlign: 'center',
              }}
            >
              <div style={{ fontWeight: 700, color: isToday ? '#4f46e5' : '#64748b', fontSize: '0.75rem' }}>{day.label.slice(0, 3)}</div>
              <div style={{ fontWeight: 900, color: isToday ? '#4f46e5' : '#0f172a', fontSize: '1.5rem', margin: '4px 0' }}>{count}</div>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>{count === 1 ? 'period' : 'periods'}</div>
            </button>
          );
        })}
      </div>

      {/* Day Detail */}
      <div style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        {/* Day Nav */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px', borderBottom: '1px solid #e2e8f0', background: '#f8fafc',
        }}>
          <button
            onClick={() => prevDay && setSelectedDay(prevDay.key)}
            disabled={!prevDay}
            style={{ padding: '8px', borderRadius: '10px', border: 'none', background: prevDay ? '#e2e8f0' : 'transparent', cursor: prevDay ? 'pointer' : 'not-allowed', opacity: prevDay ? 1 : 0.3 }}
          ><ChevronLeft size={18} color="#475569" /></button>

          <div style={{ textAlign: 'center' }}>
            <div style={{ fontWeight: 800, color: '#0f172a', fontSize: '1.05rem' }}>{todayLabel}</div>
            <div style={{ color: '#64748b', fontSize: '0.75rem' }}>{selectedSlots.length} period{selectedSlots.length !== 1 ? 's' : ''}</div>
          </div>

          <button
            onClick={() => nextDay && setSelectedDay(nextDay.key)}
            disabled={!nextDay}
            style={{ padding: '8px', borderRadius: '10px', border: 'none', background: nextDay ? '#e2e8f0' : 'transparent', cursor: nextDay ? 'pointer' : 'not-allowed', opacity: nextDay ? 1 : 0.3 }}
          ><ChevronRight size={18} color="#475569" /></button>
        </div>

        <div style={{ padding: '20px' }}>
          {slots.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px 20px', color: '#94a3b8' }}>
              <CalendarDays size={48} style={{ marginBottom: '12px', opacity: 0.3 }} />
              <p style={{ fontWeight: 600 }}>No classes assigned yet</p>
              <p style={{ fontSize: '0.85rem' }}>Your timetable will appear here once the principal sets it up.</p>
            </div>
          ) : selectedSlots.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '36px 20px', color: '#94a3b8' }}>
              <p style={{ fontWeight: 600 }}>No classes on {todayLabel}</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {selectedSlots.map(slot => {
                const style = getSubjectStyle(slot.subject);
                return (
                  <div key={slot.id} style={{
                    display: 'flex', alignItems: 'center', gap: '16px',
                    padding: '18px 20px', borderRadius: '14px',
                    border: '1px solid #e2e8f0', background: 'white',
                    transition: 'box-shadow 0.15s',
                  }}
                    onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.boxShadow = '0 4px 16px rgba(0,0,0,0.07)'}
                    onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.boxShadow = 'none'}
                  >
                    <div style={{
                      width: '50px', height: '50px', borderRadius: '14px',
                      background: style.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0,
                    }}>
                      <BookOpen size={22} color={style.color} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 800, color: '#0f172a', fontSize: '1rem' }}>{slot.subject}</div>
                      <div style={{ color: '#64748b', fontSize: '0.78rem', marginTop: '2px' }}>
                        {formatClassName(slot.class_id)} • Period {slot.period_number}
                      </div>
                    </div>
                    <div style={{
                      background: style.bg, borderRadius: '12px', padding: '10px 16px', textAlign: 'center',
                    }}>
                      <div style={{ fontWeight: 800, color: style.color, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Clock size={14} color={style.color} />{slot.start_time}
                      </div>
                      <div style={{ color: '#94a3b8', fontSize: '0.7rem', marginTop: '2px' }}>to {slot.end_time}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
