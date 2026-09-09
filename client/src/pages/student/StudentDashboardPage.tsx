import React, { useEffect, useState } from 'react';
import { Activity, BookOpen, CalendarDays, Clock, GraduationCap, RefreshCw, TrendingDown, TrendingUp, AlertCircle, FileText, ChevronRight } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { AnnouncementsWidget } from '../../components/AnnouncementsWidget';
import { apiFetch } from '../../api/client';

interface StudentDashboardPageProps {
  onNavigate?: (page: string) => void;
}

export const StudentDashboardPage: React.FC<StudentDashboardPageProps> = ({ onNavigate }) => {
  const { token, currentUser } = useAuth();
  const [attendance, setAttendance] = useState<any>(null);
  const [marks, setMarks] = useState<any>(null);
  const [timetable, setTimetable] = useState<any>(null);
  const [upcomingExams, setUpcomingExams] = useState<any[]>([]);
  const [pendingAssignments, setPendingAssignments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // class_id stored from demo login or localStorage
  const classId = localStorage.getItem('classpulse_class_id') || '';

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const requests: Promise<Response>[] = [
          apiFetch('/api/v1/student/attendance', { headers: { Authorization: `Bearer ${token}` } }),
          apiFetch('/api/v1/student/marks', { headers: { Authorization: `Bearer ${token}` } }),
          apiFetch('/api/v1/student/timetable', { headers: { Authorization: `Bearer ${token}` } }),
          apiFetch('/api/v1/student/upcoming-exams', { headers: { Authorization: `Bearer ${token}` } }),
          apiFetch('/api/v1/student/assignments', { headers: { Authorization: `Bearer ${token}` } }),
        ];
        const responses = await Promise.all(requests);
        const jsons = await Promise.all(responses.map(r => r.json()));
        if (jsons[0].success) setAttendance(jsons[0].data);
        if (jsons[1].success) setMarks(jsons[1].data);
        if (jsons[2]?.success) setTimetable(jsons[2].data);
        if (jsons[3]?.success) setUpcomingExams(jsons[3].data || []);
        if (jsons[4]?.success) {
          const pending = jsons[4].data?.pending || [];
          const overdue = jsons[4].data?.overdue || [];
          setPendingAssignments([...overdue, ...pending]);
        }
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
        <p style={{ color: '#64748b' }}>Loading your dashboard...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  const attSummary = attendance?.summary;
  const recentMarks = marks?.results?.slice(-3) || [];
  const avgPct = marks?.average_percentage;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Welcome banner */}
      <div style={{
        background: 'linear-gradient(135deg, #0c4a6e 0%, #0891b2 100%)',
        borderRadius: '20px', padding: '32px 36px', color: 'white',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', top: '-30px', right: '-30px', width: '180px', height: '180px', borderRadius: '50%', background: 'rgba(255,255,255,0.06)' }} />
        <div style={{ position: 'absolute', bottom: '-40px', right: '100px', width: '120px', height: '120px', borderRadius: '50%', background: 'rgba(255,255,255,0.04)' }} />
        <div style={{ position: 'relative' }}>
          <p style={{ opacity: 0.7, fontSize: '0.85rem', margin: '0 0 6px 0', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Welcome back</p>
          <h1 style={{ fontSize: '2rem', fontWeight: 900, margin: '0 0 8px 0', letterSpacing: '-0.02em' }}>
            {currentUser?.name?.replace(' (Student)', '') || 'Student'} 👋
          </h1>
          <p style={{ opacity: 0.8, fontSize: '0.9rem', margin: 0 }}>
            Here's your academic summary for today.
          </p>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
        {[
          {
            label: 'Attendance',
            value: attSummary?.attendance_percentage !== null && attSummary?.attendance_percentage !== undefined
              ? `${attSummary.attendance_percentage}%` : 'N/A',
            sub: `${attSummary?.present || 0} present, ${attSummary?.absent || 0} absent`,
            icon: CalendarDays, color: '#0891b2', bg: '#e0f2fe',
          },
          {
            label: 'Avg Score',
            value: avgPct !== null && avgPct !== undefined ? `${avgPct}%` : 'N/A',
            sub: `${marks?.total_exams || 0} exams`,
            icon: GraduationCap, color: '#4f46e5', bg: '#eef2ff',
          },
          {
            label: 'Days Present',
            value: attSummary?.present || 0,
            sub: `out of ${attSummary?.total || 0} days`,
            icon: Activity, color: '#059669', bg: '#d1fae5',
          },
          {
            label: 'Days Absent',
            value: attSummary?.absent || 0,
            sub: `${attSummary?.late || 0} late`,
            icon: TrendingDown, color: '#ef4444', bg: '#fef2f2',
          },
        ].map(({ label, value, sub, icon: Icon, color, bg }) => (
          <div key={label} style={{
            background: 'white', borderRadius: '16px', padding: '20px',
            border: '1px solid #e2e8f0',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <p style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', margin: '0 0 6px 0' }}>{label}</p>
                <p style={{ fontSize: '1.8rem', fontWeight: 800, color, margin: '0 0 4px 0', lineHeight: 1 }}>{value}</p>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: 0 }}>{sub}</p>
              </div>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={20} color={color} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Announcements from Principal */}
      <AnnouncementsWidget
        compact={true}
        maxItems={2}
        onViewAll={onNavigate ? () => onNavigate('student-announcements') : undefined}
      />

      {/* Recent marks */}
      <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
        <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '16px', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BookOpen size={18} color="#0891b2" /> Recent Exam Results
        </h3>
        {recentMarks.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
            No exam results yet. Your marks will appear here after your teacher enters them.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {recentMarks.map((r: any, i: number) => {
              const gradeColors: Record<string, string> = { 'A+': '#16a34a', 'A': '#22c55e', 'B': '#2563eb', 'C': '#d97706', 'D': '#ea580c', 'F': '#dc2626' };
              const gradeColor = gradeColors[r.grade] || '#64748b';
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '14px 18px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0',
                }}>
                  <div>
                    <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.9rem' }}>{r.exam_name}</div>
                    <div style={{ color: '#64748b', fontSize: '0.78rem', marginTop: '2px' }}>
                      {r.subject} • {r.exam_date}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{r.obtained_marks}/{r.max_marks}</div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: gradeColor }}>
                        {r.percentage.toFixed(1)}%
                      </div>
                    </div>
                    <div style={{
                      width: '40px', height: '40px', borderRadius: '10px',
                      background: gradeColor + '18',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '1rem', fontWeight: 800, color: gradeColor,
                    }}>
                      {r.grade}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Today's Classes / Schedule */}
      {timetable && (
        <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '16px', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={18} color="#0891b2" /> {timetable.is_sunday || (!timetable.today_slots || timetable.today_slots.length === 0) ? "Today's Schedule" : "Today's Classes"}
            <span style={{ marginLeft: '4px', background: '#e0f2fe', color: '#0369a1', padding: '2px 8px', borderRadius: '20px', fontSize: '0.72rem', fontWeight: 700 }}>
              {timetable.is_sunday ? 'Sunday' : timetable.today_label}
            </span>
          </h3>

          {timetable.today_slots && timetable.today_slots.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {timetable.today_slots.map((slot: any) => (
                <div key={slot.id} style={{
                  display: 'flex', alignItems: 'center', gap: '14px',
                  padding: '12px 16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0',
                }}>
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '10px',
                    background: '#e0f2fe', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 800, color: '#0891b2', fontSize: '0.85rem', flexShrink: 0,
                  }}>
                    P{slot.period_number}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.88rem' }}>{slot.subject}</div>
                    <div style={{ color: '#64748b', fontSize: '0.75rem' }}>{slot.teacher_name}</div>
                  </div>
                  <div style={{ fontWeight: 700, color: '#0891b2', fontSize: '0.82rem', whiteSpace: 'nowrap' }}>
                    {slot.start_time} – {slot.end_time}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{
              background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0',
              padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '1.25rem' }}>🎉</span>
                <div>
                  <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.92rem' }}>
                    No classes scheduled today
                  </div>
                  <div style={{ color: '#64748b', fontSize: '0.78rem' }}>
                    Enjoy your free day!
                  </div>
                </div>
              </div>

              {timetable.next_day_slots && timetable.next_day_slots.length > 0 && (
                <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '14px', marginTop: '2px' }}>
                  <div style={{
                    fontSize: '0.75rem', fontWeight: 700, color: '#475569',
                    textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px',
                  }}>
                    Next Classes: {timetable.next_day_label || 'Monday'}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {timetable.next_day_slots.slice(0, 4).map((slot: any) => (
                      <div key={slot.id} style={{
                        display: 'flex', alignItems: 'center', gap: '14px',
                        padding: '10px 14px', background: 'white', borderRadius: '10px', border: '1px solid #e2e8f0',
                      }}>
                        <div style={{
                          width: '32px', height: '32px', borderRadius: '8px',
                          background: '#e0f2fe', display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontWeight: 800, color: '#0891b2', fontSize: '0.8rem', flexShrink: 0,
                        }}>
                          P{slot.period_number}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.85rem' }}>{slot.subject}</div>
                          <div style={{ color: '#64748b', fontSize: '0.72rem' }}>{slot.teacher_name}</div>
                        </div>
                        <div style={{ fontWeight: 700, color: '#0891b2', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                          {slot.start_time} – {slot.end_time}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Upcoming Exams */}
      {upcomingExams.length > 0 && (
        <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontWeight: 700, color: '#0f172a', marginBottom: '16px', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={18} color="#f59e0b" /> Upcoming Exams
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {upcomingExams.slice(0, 5).map((exam: any) => {
              const urgencyStyles: Record<string, { bg: string; color: string; label: string }> = {
                TODAY:     { bg: '#fef2f2', color: '#dc2626', label: 'TODAY' },
                TOMORROW:  { bg: '#fff7ed', color: '#ea580c', label: 'TOMORROW' },
                THIS_WEEK: { bg: '#fffbeb', color: '#d97706', label: `${exam.days_remaining}d left` },
                UPCOMING:  { bg: '#f0fdf4', color: '#16a34a', label: `${exam.days_remaining}d left` },
              };
              const urgStyle = urgencyStyles[exam.urgency] || urgencyStyles.UPCOMING;
              return (
                <div key={exam.id} style={{
                  display: 'flex', alignItems: 'center', gap: '14px',
                  padding: '14px 18px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0',
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.9rem' }}>{exam.exam_name}</div>
                    <div style={{ color: '#64748b', fontSize: '0.78rem', marginTop: '2px' }}>
                      {exam.subject} • {exam.exam_date}
                      {exam.start_time && ` • ${exam.start_time}`}
                    </div>
                    {exam.description && (
                      <div style={{ color: '#94a3b8', fontSize: '0.72rem', marginTop: '2px' }}>{exam.description}</div>
                    )}
                  </div>
                  <div style={{
                    background: urgStyle.bg, color: urgStyle.color,
                    padding: '4px 12px', borderRadius: '20px',
                    fontSize: '0.72rem', fontWeight: 800, whiteSpace: 'nowrap',
                  }}>
                    {urgStyle.label}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Pending Assignments */}
      {pendingAssignments.length > 0 && (
        <div style={{ background: 'white', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontWeight: 700, color: '#0f172a', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
              <FileText size={18} color="#0891b2" /> Pending Assignments & Classwork
            </h3>
            {onNavigate && (
              <button
                onClick={() => onNavigate('student-assignments')}
                style={{
                  display: 'flex', alignItems: 'center', gap: '4px',
                  background: 'none', border: 'none', color: '#0891b2',
                  fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer',
                }}
              >
                View all <ChevronRight size={14} />
              </button>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {pendingAssignments.slice(0, 4).map((item: any) => {
              const a = item.assignment;
              const isOverdue = item.urgency === 'OVERDUE';
              return (
                <div key={a.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '14px',
                  padding: '12px 16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0',
                }}>
                  <div>
                    <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.9rem' }}>{a.title}</div>
                    <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '2px' }}>
                      {a.subject} • Due: {a.due_date} at {a.due_time} ({a.max_marks} pts)
                    </div>
                  </div>

                  <span style={{
                    background: isOverdue ? '#fee2e2' : item.urgency === 'DUE_TODAY' ? '#fee2e2' : '#e0f2fe',
                    color: isOverdue ? '#b91c1c' : item.urgency === 'DUE_TODAY' ? '#dc2626' : '#0369a1',
                    fontSize: '0.72rem', fontWeight: 800, padding: '3px 10px', borderRadius: '999px', whiteSpace: 'nowrap',
                  }}>
                    {isOverdue ? 'Overdue' : item.urgency === 'DUE_TODAY' ? 'Due Today' : `${item.days_remaining}d left`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
