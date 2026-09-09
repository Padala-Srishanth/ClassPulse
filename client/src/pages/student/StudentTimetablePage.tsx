import React, { useEffect, useState } from 'react';
import {
  BookOpen, CalendarDays, Clock, RefreshCw,
  ChevronLeft, ChevronRight, AlertCircle
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
  'Computer Science': { bg: '#f5f3ff', color: '#7c3aed' },
  'Physical Education': { bg: '#fff1f2', color: '#e11d48' },
};

function getSubjectStyle(subject: string) {
  return SUBJECT_COLORS[subject] || { bg: '#f8fafc', color: '#0891b2' };
}

export const StudentTimetablePage: React.FC = () => {
  const { token, currentUser } = useAuth();
  const [timetableData, setTimetableData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<string>('');

  // Stored class_id from profile (in demo, pulled from localStorage or default)
  const classId = localStorage.getItem('classpulse_class_id') || 'demo-class-001';

  useEffect(() => {
    // Determine today's day
    const dayMap: Record<number, string> = { 0: 'SAT', 1: 'MON', 2: 'TUE', 3: 'WED', 4: 'THU', 5: 'FRI', 6: 'SAT' };
    const todayKey = dayMap[new Date().getDay()] || 'MON';
    setSelectedDay(todayKey);
  }, []);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiFetch('/api/v1/student/timetable', {
          headers: { Authorization: `Bearer ${token}` },
        });
        const json = await res.json();
        if (json.success) {
          setTimetableData(json.data);
        } else {
          setError(json.error?.message || 'Failed to load timetable');
        }
      } catch (e: any) {
        setError(e.message || 'Network error');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [token]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px', flexDirection: 'column', gap: '16px' }}>
        <RefreshCw size={32} color="#0891b2" style={{ animation: 'spin 1s linear infinite' }} />
        <p style={{ color: '#64748b' }}>Loading your timetable...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  const grouped = timetableData?.grouped || {};
  const todaySlots = timetableData?.today_slots || [];
  const selectedSlots: any[] = grouped[selectedDay]?.slots || [];
  const allEmpty = Object.keys(grouped).length === 0;

  const dayIndex = DAYS.findIndex(d => d.key === selectedDay);
  const prevDay = dayIndex > 0 ? DAYS[dayIndex - 1] : null;
  const nextDay = dayIndex < DAYS.length - 1 ? DAYS[dayIndex + 1] : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #0c4a6e 0%, #0891b2 100%)',
        borderRadius: '20px', padding: '28px 32px', color: 'white',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', top: '-30px', right: '-30px', width: '160px', height: '160px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
        <div style={{ position: 'relative' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <CalendarDays size={22} color="#7dd3fc" />
            <span style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', opacity: 0.8 }}>Weekly Timetable</span>
          </div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 900, margin: 0, letterSpacing: '-0.02em' }}>My Schedule</h1>
          <p style={{ opacity: 0.75, margin: '6px 0 0', fontSize: '0.9rem' }}>
            {timetableData?.today_label ? `Today (${timetableData.today_label}): ${todaySlots.length} period${todaySlots.length !== 1 ? 's' : ''}` : 'Your class timetable'}
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

      {/* Today's Quick View */}
      {todaySlots.length > 0 && (
        <div style={{ background: 'linear-gradient(135deg, #eff6ff, #e0f2fe)', borderRadius: '16px', padding: '20px', border: '1px solid #bae6fd' }}>
          <h3 style={{ fontWeight: 700, color: '#0c4a6e', marginBottom: '14px', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={17} color="#0891b2" /> Today's Classes
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {todaySlots.map((slot: any) => {
              const style = getSubjectStyle(slot.subject);
              return (
                <div key={slot.id} style={{
                  display: 'flex', alignItems: 'center', gap: '14px',
                  background: 'white', borderRadius: '10px', padding: '12px 16px',
                  border: '1px solid #e2e8f0',
                }}>
                  <div style={{
                    width: '38px', height: '38px', borderRadius: '10px',
                    background: style.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  }}>
                    <BookOpen size={18} color={style.color} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.9rem' }}>{slot.subject}</div>
                    <div style={{ color: '#64748b', fontSize: '0.75rem' }}>{slot.teacher_name}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, color: style.color, fontSize: '0.85rem' }}>{slot.start_time} – {slot.end_time}</div>
                    <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>Period {slot.period_number}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Day Tabs */}
      <div style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        {/* Day Selector Header */}
        <div style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
          <button
            onClick={() => prevDay && setSelectedDay(prevDay.key)}
            disabled={!prevDay}
            style={{ padding: '14px 16px', border: 'none', background: 'transparent', cursor: prevDay ? 'pointer' : 'not-allowed', opacity: prevDay ? 1 : 0.3, color: '#475569' }}
          >
            <ChevronLeft size={18} />
          </button>
          <div style={{ flex: 1, display: 'flex', overflowX: 'auto', scrollbarWidth: 'none' }}>
            {DAYS.map(day => {
              const isActive = selectedDay === day.key;
              const hasSlots = (grouped[day.key]?.slots?.length || 0) > 0;
              return (
                <button
                  key={day.key}
                  onClick={() => setSelectedDay(day.key)}
                  style={{
                    flex: '0 0 auto', padding: '14px 16px',
                    border: 'none', borderBottom: isActive ? '3px solid #0891b2' : '3px solid transparent',
                    background: 'transparent', cursor: 'pointer',
                    color: isActive ? '#0891b2' : '#64748b',
                    fontWeight: isActive ? 700 : 500, fontSize: '0.8rem',
                    whiteSpace: 'nowrap', transition: 'all 0.15s',
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
                  }}
                >
                  {day.key}
                  {hasSlots && (
                    <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: isActive ? '#0891b2' : '#94a3b8' }} />
                  )}
                </button>
              );
            })}
          </div>
          <button
            onClick={() => nextDay && setSelectedDay(nextDay.key)}
            disabled={!nextDay}
            style={{ padding: '14px 16px', border: 'none', background: 'transparent', cursor: nextDay ? 'pointer' : 'not-allowed', opacity: nextDay ? 1 : 0.3, color: '#475569' }}
          >
            <ChevronRight size={18} />
          </button>
        </div>

        {/* Selected Day Content */}
        <div style={{ padding: '20px' }}>
          <div style={{ fontWeight: 700, color: '#0f172a', marginBottom: '16px', fontSize: '0.95rem' }}>
            {DAYS.find(d => d.key === selectedDay)?.label} Schedule
          </div>

          {allEmpty ? (
            <div style={{ textAlign: 'center', padding: '48px 20px', color: '#94a3b8' }}>
              <CalendarDays size={48} style={{ marginBottom: '12px', opacity: 0.4 }} />
              <p style={{ fontWeight: 600, marginBottom: '6px' }}>No timetable set yet</p>
              <p style={{ fontSize: '0.85rem' }}>Your principal hasn't added the class timetable yet.</p>
            </div>
          ) : selectedSlots.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '36px 20px', color: '#94a3b8' }}>
              <p style={{ fontWeight: 600, marginBottom: '4px' }}>No classes scheduled</p>
              <p style={{ fontSize: '0.85rem' }}>No periods on {DAYS.find(d => d.key === selectedDay)?.label}.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {selectedSlots.map((slot: any) => {
                const style = getSubjectStyle(slot.subject);
                return (
                  <div key={slot.id} style={{
                    display: 'flex', alignItems: 'center', gap: '16px',
                    padding: '16px 20px', borderRadius: '12px',
                    border: '1px solid #e2e8f0',
                    background: 'white',
                    transition: 'box-shadow 0.15s',
                  }}
                    onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.boxShadow = '0 2px 12px rgba(0,0,0,0.06)'}
                    onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.boxShadow = 'none'}
                  >
                    {/* Period badge */}
                    <div style={{
                      width: '44px', height: '44px', borderRadius: '12px',
                      background: style.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, fontSize: '1.1rem', fontWeight: 800, color: style.color,
                    }}>
                      {slot.period_number}
                    </div>
                    {/* Subject info */}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.95rem' }}>{slot.subject}</div>
                      <div style={{ color: '#64748b', fontSize: '0.78rem', marginTop: '2px' }}>
                        {slot.teacher_name}
                      </div>
                    </div>
                    {/* Time */}
                    <div style={{
                      background: style.bg, borderRadius: '10px', padding: '8px 14px',
                      textAlign: 'center',
                    }}>
                      <div style={{ fontWeight: 700, color: style.color, fontSize: '0.9rem', whiteSpace: 'nowrap' }}>
                        {slot.start_time}
                      </div>
                      <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>to {slot.end_time}</div>
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
