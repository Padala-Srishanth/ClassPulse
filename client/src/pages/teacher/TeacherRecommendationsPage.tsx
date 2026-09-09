import React, { useEffect, useState, useMemo } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Calendar,
  CheckCircle2,
  ChevronDown,
  Clock,
  Filter,
  Flame,
  HelpCircle,
  Lightbulb,
  PhoneCall,
  RefreshCw,
  Search,
  Sparkles,
  TrendingDown,
  User,
  Users,
  X,
  XCircle,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { recommendationsApi } from '../../api/recommendations';
import { classesApi } from '../../api/classes';
import {
  InterventionRecommendation,
  InterventionType,
  PriorityLevel,
  RecommendationStatus,
  SchoolClass,
} from '../../types';

interface TeacherRecommendationsPageProps {
  onSelectStudent?: (studentId: string) => void;
}

export const TeacherRecommendationsPage: React.FC<TeacherRecommendationsPageProps> = ({
  onSelectStudent,
}) => {
  const { schoolId, currentUser } = useAuth();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [recommendations, setRecommendations] = useState<InterventionRecommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Modal states
  const [approvingRec, setApprovingRec] = useState<InterventionRecommendation | null>(null);
  const [approveType, setApproveType] = useState<InterventionType>('ONE_ON_ONE_CHECKIN');
  const [approveNotes, setApproveNotes] = useState<string>('');
  const [approveFollowUp, setApproveFollowUp] = useState<string>('');
  const [submittingApprove, setSubmittingApprove] = useState<boolean>(false);

  const [dismissingRec, setDismissingRec] = useState<InterventionRecommendation | null>(null);
  const [dismissReason, setDismissReason] = useState<string>('TEACHER_JUDGMENT');
  const [dismissNotes, setDismissNotes] = useState<string>('');
  const [submittingDismiss, setSubmittingDismiss] = useState<boolean>(false);

  // Success toast
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // 1. Fetch Classes
  useEffect(() => {
    if (!schoolId) return;
    classesApi.listSchoolClasses(schoolId).then((clsList) => {
      setClasses(clsList);
    }).catch(console.error);
  }, [schoolId]);

  // 2. Fetch Recommendations
  const fetchRecommendations = async () => {
    if (!schoolId) return;
    setLoading(true);
    try {
      if (selectedClassId !== 'ALL') {
        const data = await recommendationsApi.getClassRecommendations(selectedClassId);
        setRecommendations(data);
      } else {
        const data = await recommendationsApi.getSchoolRecommendations(schoolId);
        setRecommendations(data);
      }
    } catch (err) {
      console.error('Failed to load recommendations:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [schoolId, selectedClassId]);

  // Filtered recommendations
  const filteredRecs = useMemo(() => {
    return recommendations.filter((r) => {
      // Status filter
      if (statusFilter !== 'ALL' && r.status !== statusFilter) return false;
      // Priority filter
      if (priorityFilter !== 'ALL' && r.priority_level !== priorityFilter) return false;
      // Search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = r.student_name?.toLowerCase().includes(q);
        const matchesType = r.recommendation_type.toLowerCase().includes(q);
        const matchesReason = r.explanation.toLowerCase().includes(q);
        if (!matchesName && !matchesType && !matchesReason) return false;
      }
      return true;
    });
  }, [recommendations, statusFilter, priorityFilter, searchQuery]);

  // Metrics summary
  const metrics = useMemo(() => {
    const pending = recommendations.filter((r) => r.status === 'PENDING');
    const urgent = pending.filter((r) => r.priority_level === 'URGENT').length;
    const high = pending.filter((r) => r.priority_level === 'HIGH').length;
    const approved = recommendations.filter((r) => r.status === 'CONVERTED_TO_INTERVENTION').length;
    return {
      totalPending: pending.length,
      urgent,
      high,
      approved,
    };
  }, [recommendations]);

  // Open Approve Modal
  const handleOpenApprove = (rec: InterventionRecommendation) => {
    setApprovingRec(rec);
    setApproveType(rec.recommendation_type);
    setApproveNotes(rec.explanation);
    const date = new Date();
    date.setDate(date.getDate() + (rec.suggested_follow_up_days || 7));
    setApproveFollowUp(date.toISOString().split('T')[0]);
  };

  // Submit Approval
  const handleSubmitApprove = async () => {
    if (!approvingRec) return;
    setSubmittingApprove(true);
    try {
      await recommendationsApi.approveRecommendation(approvingRec.recommendation_id, {
        type: approveType,
        notes: approveNotes,
        follow_up_date: approveFollowUp || undefined,
      });
      showToast(`Intervention created for ${approvingRec.student_name || 'student'}.`);
      setApprovingRec(null);
      fetchRecommendations();
    } catch (err: any) {
      alert(err.message || 'Failed to approve recommendation');
    } finally {
      setSubmittingApprove(false);
    }
  };

  // Open Dismiss Modal
  const handleOpenDismiss = (rec: InterventionRecommendation) => {
    setDismissingRec(rec);
    setDismissReason('TEACHER_JUDGMENT');
    setDismissNotes('');
  };

  // Submit Dismissal
  const handleSubmitDismiss = async () => {
    if (!dismissingRec) return;
    setSubmittingDismiss(true);
    try {
      await recommendationsApi.dismissRecommendation(dismissingRec.recommendation_id, {
        reason: dismissReason,
        notes: dismissNotes || undefined,
      });
      showToast(`Recommendation dismissed.`);
      setDismissingRec(null);
      fetchRecommendations();
    } catch (err: any) {
      alert(err.message || 'Failed to dismiss recommendation');
    } finally {
      setSubmittingDismiss(false);
    }
  };

  const getPriorityBadge = (p: PriorityLevel) => {
    switch (p) {
      case 'URGENT':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px', borderRadius: 999, background: '#fee2e2', color: '#b91c1c', fontSize: '0.75rem', fontWeight: 700, border: '1px solid #fca5a5' }}>
            <Flame size={13} /> URGENT
          </span>
        );
      case 'HIGH':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px', borderRadius: 999, background: '#ffedd5', color: '#c2410c', fontSize: '0.75rem', fontWeight: 700, border: '1px solid #fdba74' }}>
            <AlertTriangle size={13} /> HIGH
          </span>
        );
      case 'MEDIUM':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px', borderRadius: 999, background: '#e0f2fe', color: '#0369a1', fontSize: '0.75rem', fontWeight: 600, border: '1px solid #7dd3fc' }}>
            MEDIUM
          </span>
        );
      default:
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px', borderRadius: 999, background: '#f1f5f9', color: '#475569', fontSize: '0.75rem', fontWeight: 600, border: '1px solid #cbd5e1' }}>
            LOW
          </span>
        );
    }
  };

  const getTypeLabelAndIcon = (type: InterventionType) => {
    switch (type) {
      case 'ONE_ON_ONE_CHECKIN':
      case 'ONE_ON_ONE_SUPPORT':
        return { label: 'One-on-One Check-in', icon: User, color: '#4f46e5' };
      case 'ACADEMIC_SUPPORT':
        return { label: 'Academic Support Clinic', icon: BookOpen, color: '#0284c7' };
      case 'PARENT_CONTACT':
        return { label: 'Parent Advisory Contact', icon: PhoneCall, color: '#d97706' };
      case 'ATTENDANCE_SUPPORT':
        return { label: 'Attendance Mentorship', icon: Clock, color: '#059669' };
      case 'EXTRA_ASSIGNMENT':
        return { label: 'Remedial Practice Assignment', icon: BookOpen, color: '#7c3aed' };
      case 'COUNSELING_REFERRAL':
        return { label: 'Counseling & Student Welfare', icon: HeartIcon, color: '#dc2626' };
      case 'FOLLOW_UP_REVIEW':
        return { label: 'Intervention Progress Review', icon: RefreshCw, color: '#2563eb' };
      default:
        return { label: type.replace(/_/g, ' '), icon: Lightbulb, color: '#475569' };
    }
  };

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Toast */}
      {toastMessage && (
        <div
          style={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            background: '#0f172a',
            color: '#fff',
            padding: '12px 20px',
            borderRadius: 8,
            boxShadow: '0 10px 25px -5px rgba(0,0,0,0.3)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            zIndex: 9999,
            fontSize: '0.9rem',
          }}
        >
          <CheckCircle2 size={18} color="#4ade80" />
          {toastMessage}
        </div>
      )}

      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%)',
          borderRadius: 16,
          padding: '28px 32px',
          color: '#ffffff',
          marginBottom: 24,
          boxShadow: '0 10px 25px -5px rgba(49, 46, 129, 0.25)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <div style={{ background: 'rgba(255,255,255,0.15)', padding: 6, borderRadius: 8 }}>
              <Sparkles size={22} color="#fde047" />
            </div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: 700, letterSpacing: '-0.02em', margin: 0 }}>
              Smart Intervention Recommendations
            </h1>
          </div>
          <p style={{ color: '#c7d2fe', fontSize: '0.95rem', margin: 0, maxWidth: 650, lineHeight: 1.5 }}>
            Automated, explainable decision support answering <strong>"What should the educator do next?"</strong>. Every action remains advisory until you approve or adjust.
          </p>
        </div>

        <button
          onClick={() => {
            setRefreshing(true);
            fetchRecommendations();
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: 'rgba(255,255,255,0.15)',
            border: '1px solid rgba(255,255,255,0.25)',
            color: '#fff',
            padding: '10px 18px',
            borderRadius: 8,
            fontSize: '0.9rem',
            fontWeight: 600,
            cursor: 'pointer',
            backdropFilter: 'blur(4px)',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.25)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.15)')}
        >
          <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          Refresh Recommendations
        </button>
      </div>

      {/* KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 16,
          marginBottom: 24,
        }}
      >
        <div style={{ background: '#fff', borderRadius: 12, padding: '18px 20px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>
            Pending Recommendations
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#0f172a' }}>
            {metrics.totalPending}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 4 }}>Awaiting educator review</div>
        </div>

        <div style={{ background: '#fff', borderRadius: 12, padding: '18px 20px', border: '1px solid #fee2e2', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', color: '#dc2626', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Flame size={15} /> Urgent Actions
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#b91c1c' }}>
            {metrics.urgent}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#ef4444', marginTop: 4 }}>Severe / multi-signal drops</div>
        </div>

        <div style={{ background: '#fff', borderRadius: 12, padding: '18px 20px', border: '1px solid #ffedd5', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', color: '#ea580c', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
            <AlertTriangle size={15} /> High Priority
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#c2410c' }}>
            {metrics.high}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#f97316', marginTop: 4 }}>Persistent or sudden declines</div>
        </div>

        <div style={{ background: '#fff', borderRadius: 12, padding: '18px 20px', border: '1px solid #dcfce7', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', color: '#16a34a', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
            <CheckCircle2 size={15} /> In-Motion / Converted
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#15803d' }}>
            {metrics.approved}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#22c55e', marginTop: 4 }}>Interventions currently active</div>
        </div>
      </div>

      {/* Filter Controls */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: 12,
          padding: '16px 20px',
          border: '1px solid #e2e8f0',
          marginBottom: 24,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 14,
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center', flex: 1, minWidth: 300 }}>
          {/* Search */}
          <div style={{ position: 'relative', minWidth: 220 }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
            <input
              type="text"
              placeholder="Search student or action..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                padding: '8px 12px 8px 36px',
                borderRadius: 8,
                border: '1px solid #cbd5e1',
                fontSize: '0.85rem',
                width: '100%',
                outline: 'none',
              }}
            />
          </div>

          {/* Class Select */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Class:</span>
            <select
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#fff', outline: 'none' }}
            >
              <option value="ALL">All Assigned Classes</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Priority Select */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Priority:</span>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#fff', outline: 'none' }}
            >
              <option value="ALL">All Priorities</option>
              <option value="URGENT">Urgent Only</option>
              <option value="HIGH">High Priority</option>
              <option value="MEDIUM">Medium Priority</option>
              <option value="LOW">Low Priority</option>
            </select>
          </div>

          {/* Status Select */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#fff', outline: 'none' }}
            >
              <option value="PENDING">Pending Review</option>
              <option value="CONVERTED_TO_INTERVENTION">Converted / Approved</option>
              <option value="DISMISSED">Dismissed</option>
              <option value="ALL">All Statuses</option>
            </select>
          </div>
        </div>

        <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 500 }}>
          Showing <strong>{filteredRecs.length}</strong> recommendations
        </div>
      </div>

      {/* Loading state */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0' }}>
          <RefreshCw size={32} className="animate-spin" color="#4f46e5" style={{ margin: '0 auto 16px' }} />
          <p style={{ color: '#64748b', fontSize: '0.95rem' }}>Synthesizing smart intervention recommendations...</p>
        </div>
      ) : filteredRecs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0' }}>
          <CheckCircle2 size={40} color="#10b981" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: '#1e293b', marginBottom: 6 }}>
            No Recommendations Found
          </h3>
          <p style={{ color: '#64748b', fontSize: '0.9rem', maxWidth: 450, margin: '0 auto' }}>
            No students match the current filters. Your students are performing stably or all pending items have been addressed.
          </p>
        </div>
      ) : (
        /* Recommendations Cards Feed */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          {filteredRecs.map((rec) => {
            const { label: typeLabel, icon: TypeIcon, color: typeColor } = getTypeLabelAndIcon(rec.recommendation_type);

            return (
              <div
                key={rec.recommendation_id}
                style={{
                  background: '#ffffff',
                  borderRadius: 14,
                  border: rec.priority_level === 'URGENT' ? '2px solid #f87171' : '1px solid #e2e8f0',
                  boxShadow: rec.priority_level === 'URGENT' ? '0 4px 20px rgba(239, 68, 68, 0.08)' : '0 2px 8px rgba(0,0,0,0.04)',
                  padding: '22px 26px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                }}
              >
                {/* Card Top Row: Student, Class, Badges, Priority */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                      <h3
                        onClick={() => onSelectStudent && onSelectStudent(rec.student_id)}
                        style={{
                          fontSize: '1.15rem',
                          fontWeight: 700,
                          color: '#0f172a',
                          margin: 0,
                          cursor: onSelectStudent ? 'pointer' : 'default',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        {rec.student_name || 'Student'}
                        {onSelectStudent && <ArrowRight size={15} color="#6366f1" />}
                      </h3>

                      <span style={{ fontSize: '0.8rem', padding: '2px 8px', borderRadius: 6, background: '#f1f5f9', color: '#475569', fontWeight: 600 }}>
                        {rec.class_name || 'Class'}
                      </span>

                      {rec.risk_score !== undefined && (
                        <span style={{ fontSize: '0.8rem', padding: '2px 8px', borderRadius: 6, background: rec.risk_score >= 60 ? '#fee2e2' : rec.risk_score >= 30 ? '#ffedd5' : '#f0fdf4', color: rec.risk_score >= 60 ? '#b91c1c' : rec.risk_score >= 30 ? '#c2410c' : '#15803d', fontWeight: 600 }}>
                          Risk: {rec.risk_score} ({rec.risk_level || 'EVAL'})
                        </span>
                      )}

                      {rec.status === 'CONVERTED_TO_INTERVENTION' && (
                        <span style={{ fontSize: '0.75rem', padding: '3px 8px', borderRadius: 999, background: '#dcfce7', color: '#16a34a', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                          <CheckCircle2 size={13} /> Active Intervention
                        </span>
                      )}

                      {rec.status === 'DISMISSED' && (
                        <span style={{ fontSize: '0.75rem', padding: '3px 8px', borderRadius: 999, background: '#f1f5f9', color: '#64748b', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                          <XCircle size={13} /> Dismissed: {rec.dismissal_reason?.replace(/_/g, ' ')}
                        </span>
                      )}
                    </div>

                    {/* Declining Signals Pills */}
                    <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
                      {Boolean(rec.signals_summary?.attendance_drop && rec.signals_summary.attendance_drop > 0) && (
                        <span style={{ fontSize: '0.75rem', background: '#fee2e2', color: '#991b1b', padding: '2px 8px', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 4, fontWeight: 500 }}>
                          <TrendingDown size={13} /> Attendance ↓ {rec.signals_summary?.attendance_drop}%
                        </span>
                      )}
                      {Boolean(rec.signals_summary?.homework_drop && rec.signals_summary.homework_drop > 0) && (
                        <span style={{ fontSize: '0.75rem', background: '#fef3c7', color: '#92400e', padding: '2px 8px', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 4, fontWeight: 500 }}>
                          <TrendingDown size={13} /> Homework ↓ {rec.signals_summary?.homework_drop}%
                        </span>
                      )}
                      {Boolean(rec.signals_summary?.academic_drop && rec.signals_summary.academic_drop > 0) && (
                        <span style={{ fontSize: '0.75rem', background: '#e0e7ff', color: '#3730a3', padding: '2px 8px', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 4, fontWeight: 500 }}>
                          <TrendingDown size={13} /> Academics ↓ {rec.signals_summary?.academic_drop}%
                        </span>
                      )}
                      {rec.signals_summary?.is_persistent && (
                        <span style={{ fontSize: '0.75rem', background: '#fce7f3', color: '#9d174d', padding: '2px 8px', borderRadius: 6, fontWeight: 600 }}>
                          Persistent Drop
                        </span>
                      )}
                      {rec.signals_summary?.is_sudden_drop && (
                        <span style={{ fontSize: '0.75rem', background: '#fee2e2', color: '#b91c1c', padding: '2px 8px', borderRadius: 6, fontWeight: 700 }}>
                          ⚡ Sudden Drop
                        </span>
                      )}
                      {rec.signals_summary?.is_stable_low && (
                        <span style={{ fontSize: '0.75rem', background: '#e0f2fe', color: '#0369a1', padding: '2px 8px', borderRadius: 6, fontWeight: 500 }}>
                          Stable Low Baseline
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Priority Badge */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 500 }}>
                      Score: {rec.priority_score.toFixed(0)}
                    </span>
                    {getPriorityBadge(rec.priority_level)}
                  </div>
                </div>

                {/* Card Middle: Recommended Action & Explanation */}
                <div
                  style={{
                    background: '#f8fafc',
                    borderRadius: 10,
                    padding: '16px 20px',
                    border: '1px solid #f1f5f9',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 10,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ background: '#fff', padding: 8, borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.05)', color: typeColor }}>
                      <TypeIcon size={20} />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
                        Recommended Intervention Action
                      </div>
                      <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0f172a' }}>
                        {typeLabel}
                      </div>
                    </div>
                  </div>

                  {/* Factual Explanation */}
                  <p style={{ fontSize: '0.9rem', color: '#334155', margin: 0, lineHeight: 1.5, background: '#fff', padding: '10px 14px', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                    <strong>Why:</strong> {rec.explanation}
                  </p>

                  {/* Action Steps */}
                  {rec.recommended_actions && rec.recommended_actions.length > 0 && (
                    <div style={{ marginTop: 4 }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: 6 }}>
                        Suggested Action Plan:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: 20, fontSize: '0.85rem', color: '#475569', lineHeight: 1.6 }}>
                        {rec.recommended_actions.map((act, idx) => (
                          <li key={idx}>{act}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 6, fontSize: '0.8rem', color: '#64748b' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      <Clock size={14} /> Suggested Follow-up: <strong>{rec.suggested_follow_up_days} days</strong>
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      <Calendar size={14} /> Generated: <strong>{new Date(rec.created_at).toLocaleDateString()}</strong>
                    </span>
                  </div>
                </div>

                {/* Card Actions */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10, paddingTop: 4 }}>
                  {onSelectStudent && (
                    <button
                      onClick={() => onSelectStudent(rec.student_id)}
                      style={{
                        padding: '8px 14px',
                        borderRadius: 8,
                        border: '1px solid #cbd5e1',
                        background: '#fff',
                        color: '#334155',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      View Student Profile
                    </button>
                  )}

                  {rec.status === 'PENDING' && (
                    <>
                      <button
                        onClick={() => handleOpenDismiss(rec)}
                        style={{
                          padding: '8px 14px',
                          borderRadius: 8,
                          border: '1px solid #e2e8f0',
                          background: '#fff',
                          color: '#64748b',
                          fontSize: '0.85rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.color = '#ef4444';
                          e.currentTarget.style.borderColor = '#fca5a5';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.color = '#64748b';
                          e.currentTarget.style.borderColor = '#e2e8f0';
                        }}
                      >
                        Dismiss
                      </button>

                      <button
                        onClick={() => handleOpenApprove(rec)}
                        style={{
                          padding: '8px 18px',
                          borderRadius: 8,
                          border: 'none',
                          background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
                          color: '#fff',
                          fontSize: '0.85rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          boxShadow: '0 2px 4px rgba(79, 70, 229, 0.2)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        <CheckCircle2 size={16} /> Approve & Create Intervention
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Approve Modal */}
      {approvingRec && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20,
            backdropFilter: 'blur(3px)',
          }}
          onClick={() => setApprovingRec(null)}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 16,
              width: '100%',
              maxWidth: 580,
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)',
              overflow: 'hidden',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, color: '#0f172a' }}>
                  Approve Intervention Action
                </h3>
                <p style={{ fontSize: '0.85rem', color: '#64748b', margin: '4px 0 0' }}>
                  For student: <strong>{approvingRec.student_name}</strong> ({approvingRec.class_name})
                </p>
              </div>
              <button onClick={() => setApprovingRec(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Type select */}
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: 6 }}>
                  Intervention Action Type:
                </label>
                <select
                  value={approveType}
                  onChange={(e) => setApproveType(e.target.value as InterventionType)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                >
                  <option value="ONE_ON_ONE_CHECKIN">One-on-One Check-in</option>
                  <option value="ACADEMIC_SUPPORT">Academic Support Clinic</option>
                  <option value="ATTENDANCE_SUPPORT">Attendance Mentorship</option>
                  <option value="EXTRA_ASSIGNMENT">Remedial Extra Assignment</option>
                  <option value="PARENT_CONTACT">Parent Contact Advisory</option>
                  <option value="COUNSELING_REFERRAL">Counseling Referral</option>
                  <option value="FOLLOW_UP_REVIEW">Follow-up Review</option>
                  <option value="OTHER">Other Intervention</option>
                </select>
              </div>

              {/* Action Notes */}
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: 6 }}>
                  Action Notes & Justification:
                </label>
                <textarea
                  rows={4}
                  value={approveNotes}
                  onChange={(e) => setApproveNotes(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.9rem', resize: 'vertical' }}
                />
              </div>

              {/* Follow-up date */}
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: 6 }}>
                  Target Follow-up Date:
                </label>
                <input
                  type="date"
                  value={approveFollowUp}
                  onChange={(e) => setApproveFollowUp(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                />
              </div>
            </div>

            <div style={{ padding: '16px 24px', background: '#f8fafc', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                onClick={() => setApprovingRec(null)}
                style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#fff', color: '#475569', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitApprove}
                disabled={submittingApprove}
                style={{
                  padding: '8px 20px',
                  borderRadius: 8,
                  border: 'none',
                  background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
                  color: '#fff',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: submittingApprove ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                {submittingApprove ? <RefreshCw size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                Confirm & Create Intervention
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dismiss Modal */}
      {dismissingRec && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20,
            backdropFilter: 'blur(3px)',
          }}
          onClick={() => setDismissingRec(null)}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 16,
              width: '100%',
              maxWidth: 500,
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)',
              overflow: 'hidden',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0, color: '#0f172a' }}>
                Dismiss Recommendation
              </h3>
              <button onClick={() => setDismissingRec(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: 6 }}>
                  Reason for Dismissal:
                </label>
                <select
                  value={dismissReason}
                  onChange={(e) => setDismissReason(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                >
                  <option value="TEACHER_JUDGMENT">Teacher Professional Judgment</option>
                  <option value="ISSUE_ALREADY_RESOLVED">Issue Already Resolved / Recovered</option>
                  <option value="DUPLICATE_RECOMMENDATION">Duplicate or Overlapping Action</option>
                  <option value="NOT_APPLICABLE">Not Applicable (e.g. Excused Medical Leave)</option>
                  <option value="OTHER">Other Reason</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: 6 }}>
                  Optional Educator Notes:
                </label>
                <textarea
                  rows={3}
                  value={dismissNotes}
                  onChange={(e) => setDismissNotes(e.target.value)}
                  placeholder="Add any clarifying context for audit trail..."
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                />
              </div>
            </div>

            <div style={{ padding: '16px 24px', background: '#f8fafc', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                onClick={() => setDismissingRec(null)}
                style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#fff', color: '#475569', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitDismiss}
                disabled={submittingDismiss}
                style={{
                  padding: '8px 18px',
                  borderRadius: 8,
                  border: 'none',
                  background: '#ef4444',
                  color: '#fff',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: submittingDismiss ? 'not-allowed' : 'pointer',
                }}
              >
                {submittingDismiss ? 'Dismissing...' : 'Confirm Dismissal'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const HeartIcon: React.FC<{ size?: number }> = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
  </svg>
);
