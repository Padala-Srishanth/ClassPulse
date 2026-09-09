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
  Download,
  Filter,
  Flame,
  HelpCircle,
  Layers,
  Lightbulb,
  PhoneCall,
  RefreshCw,
  Search,
  Shield,
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

interface PrincipalInterventionRecommendationsPageProps {
  onSelectStudent?: (studentId: string) => void;
}

export const PrincipalInterventionRecommendationsPage: React.FC<PrincipalInterventionRecommendationsPageProps> = ({
  onSelectStudent,
}) => {
  const { schoolId } = useAuth();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [recommendations, setRecommendations] = useState<InterventionRecommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<'TABLE' | 'CARDS'>('TABLE');

  // Modal states
  const [reviewingRec, setReviewingRec] = useState<InterventionRecommendation | null>(null);
  const [approveType, setApproveType] = useState<InterventionType>('ONE_ON_ONE_CHECKIN');
  const [approveNotes, setApproveNotes] = useState<string>('');
  const [approveFollowUp, setApproveFollowUp] = useState<string>('');
  const [submittingApprove, setSubmittingApprove] = useState<boolean>(false);

  const [dismissingRec, setDismissingRec] = useState<InterventionRecommendation | null>(null);
  const [dismissReason, setDismissReason] = useState<string>('TEACHER_JUDGMENT');
  const [dismissNotes, setDismissNotes] = useState<string>('');
  const [submittingDismiss, setSubmittingDismiss] = useState<boolean>(false);

  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  useEffect(() => {
    if (!schoolId) return;
    classesApi.listSchoolClasses(schoolId).then(setClasses).catch(console.error);
  }, [schoolId]);

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
      console.error('Failed to load school recommendations:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [schoolId, selectedClassId]);

  const filteredRecs = useMemo(() => {
    return recommendations.filter((r) => {
      if (statusFilter !== 'ALL' && r.status !== statusFilter) return false;
      if (priorityFilter !== 'ALL' && r.priority_level !== priorityFilter) return false;
      if (typeFilter !== 'ALL' && r.recommendation_type !== typeFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = r.student_name?.toLowerCase().includes(q);
        const matchesType = r.recommendation_type.toLowerCase().includes(q);
        const matchesReason = r.explanation.toLowerCase().includes(q);
        if (!matchesName && !matchesType && !matchesReason) return false;
      }
      return true;
    });
  }, [recommendations, statusFilter, priorityFilter, typeFilter, searchQuery]);

  const stats = useMemo(() => {
    const pending = recommendations.filter((r) => r.status === 'PENDING');
    const urgent = pending.filter((r) => r.priority_level === 'URGENT').length;
    const high = pending.filter((r) => r.priority_level === 'HIGH').length;
    const converted = recommendations.filter((r) => r.status === 'CONVERTED_TO_INTERVENTION').length;
    const dismissed = recommendations.filter((r) => r.status === 'DISMISSED').length;
    return {
      totalPending: pending.length,
      urgent,
      high,
      converted,
      dismissed,
    };
  }, [recommendations]);

  const handleOpenApprove = (rec: InterventionRecommendation) => {
    setReviewingRec(rec);
    setApproveType(rec.recommendation_type);
    setApproveNotes(rec.explanation);
    const date = new Date();
    date.setDate(date.getDate() + (rec.suggested_follow_up_days || 7));
    setApproveFollowUp(date.toISOString().split('T')[0]);
  };

  const handleSubmitApprove = async () => {
    if (!reviewingRec) return;
    setSubmittingApprove(true);
    try {
      await recommendationsApi.approveRecommendation(reviewingRec.recommendation_id, {
        type: approveType,
        notes: approveNotes,
        follow_up_date: approveFollowUp || undefined,
      });
      showToast(`Intervention approved for ${reviewingRec.student_name || 'student'}.`);
      setReviewingRec(null);
      fetchRecommendations();
    } catch (err: any) {
      alert(err.message || 'Failed to approve recommendation');
    } finally {
      setSubmittingApprove(false);
    }
  };

  const handleOpenDismiss = (rec: InterventionRecommendation) => {
    setDismissingRec(rec);
    setDismissReason('TEACHER_JUDGMENT');
    setDismissNotes('');
  };

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
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 999, background: '#fee2e2', color: '#b91c1c', fontSize: '0.72rem', fontWeight: 700 }}>
            <Flame size={12} /> URGENT
          </span>
        );
      case 'HIGH':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 999, background: '#ffedd5', color: '#c2410c', fontSize: '0.72rem', fontWeight: 700 }}>
            <AlertTriangle size={12} /> HIGH
          </span>
        );
      case 'MEDIUM':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 999, background: '#e0f2fe', color: '#0369a1', fontSize: '0.72rem', fontWeight: 600 }}>
            MEDIUM
          </span>
        );
      default:
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 999, background: '#f1f5f9', color: '#475569', fontSize: '0.72rem', fontWeight: 600 }}>
            LOW
          </span>
        );
    }
  };

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1440, margin: '0 auto' }}>
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
          background: 'linear-gradient(135deg, #064e3b 0%, #047857 60%, #059669 100%)',
          borderRadius: 16,
          padding: '28px 32px',
          color: '#ffffff',
          marginBottom: 24,
          boxShadow: '0 10px 25px -5px rgba(4, 120, 87, 0.25)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <div style={{ background: 'rgba(255,255,255,0.2)', padding: 6, borderRadius: 8 }}>
              <Shield size={22} color="#a7f3d0" />
            </div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: 700, letterSpacing: '-0.02em', margin: 0 }}>
              Smart Student Support Recommendations
            </h1>
          </div>
          <p style={{ color: '#d1fae5', fontSize: '0.95rem', margin: 0, maxWidth: 650, lineHeight: 1.5 }}>
            School-wide intelligent intervention oversight. Monitor identified learning hurdles, evaluate automated recommendations, and sanction student support actions across all grade cohorts.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={() => {
              setRefreshing(true);
              fetchRecommendations();
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              background: 'rgba(255,255,255,0.2)',
              border: '1px solid rgba(255,255,255,0.3)',
              color: '#fff',
              padding: '10px 18px',
              borderRadius: 8,
              fontSize: '0.9rem',
              fontWeight: 600,
              cursor: 'pointer',
              backdropFilter: 'blur(4px)',
            }}
          >
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Widgets */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 16,
          marginBottom: 24,
        }}
      >
        <div style={{ background: '#fff', borderRadius: 12, padding: '18px 20px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>
            Pending Support Actions
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#0f172a' }}>{stats.totalPending}</div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 4 }}>Across all school classes</div>
        </div>

        <div style={{ background: '#fff', borderRadius: 12, padding: '18px 20px', border: '1px solid #fee2e2', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.75rem', color: '#dc2626', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 5 }}>
            <Flame size={14} /> Urgent Triggers
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#b91c1c' }}>{stats.urgent}</div>
          <div style={{ fontSize: '0.75rem', color: '#ef4444', marginTop: 4 }}>Immediate action required</div>
        </div>

        <div style={{ background: '#fff', borderRadius: 12, padding: '18px 20px', border: '1px solid #ffedd5', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.75rem', color: '#ea580c', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 5 }}>
            <AlertTriangle size={14} /> High Priority
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#c2410c' }}>{stats.high}</div>
          <div style={{ fontSize: '0.75rem', color: '#f97316', marginTop: 4 }}>Decline signals persisting</div>
        </div>

        <div style={{ background: '#fff', borderRadius: 12, padding: '18px 20px', border: '1px solid #dcfce7', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.75rem', color: '#16a34a', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 5 }}>
            <CheckCircle2 size={14} /> Converted / Active
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#15803d' }}>{stats.converted}</div>
          <div style={{ fontSize: '0.75rem', color: '#22c55e', marginTop: 4 }}>Logged into intervention plan</div>
        </div>

        <div style={{ background: '#fff', borderRadius: 12, padding: '18px 20px', border: '1px solid #f1f5f9', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 5 }}>
            <XCircle size={14} /> Dismissed Actions
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#475569' }}>{stats.dismissed}</div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 4 }}>Dismissed with rationale</div>
        </div>
      </div>

      {/* Multi-Dimensional Filters */}
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
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center', flex: 1, minWidth: 320 }}>
          <div style={{ position: 'relative', minWidth: 200 }}>
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

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Class:</span>
            <select
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#fff', outline: 'none' }}
            >
              <option value="ALL">All School Classes</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Priority:</span>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#fff', outline: 'none' }}
            >
              <option value="ALL">All Priorities</option>
              <option value="URGENT">Urgent</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Action Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#fff', outline: 'none' }}
            >
              <option value="ALL">All Action Types</option>
              <option value="ONE_ON_ONE_CHECKIN">One-on-One Check-in</option>
              <option value="ACADEMIC_SUPPORT">Academic Support</option>
              <option value="PARENT_CONTACT">Parent Contact</option>
              <option value="ATTENDANCE_SUPPORT">Attendance Mentorship</option>
              <option value="EXTRA_ASSIGNMENT">Remedial Assignment</option>
              <option value="COUNSELING_REFERRAL">Counseling Referral</option>
              <option value="FOLLOW_UP_REVIEW">Follow-up Review</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#fff', outline: 'none' }}
            >
              <option value="PENDING">Pending Review</option>
              <option value="CONVERTED_TO_INTERVENTION">Converted</option>
              <option value="DISMISSED">Dismissed</option>
              <option value="ALL">All Statuses</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ display: 'flex', background: '#f1f5f9', padding: 3, borderRadius: 8 }}>
            <button
              onClick={() => setViewMode('TABLE')}
              style={{
                padding: '6px 12px',
                borderRadius: 6,
                border: 'none',
                background: viewMode === 'TABLE' ? '#fff' : 'transparent',
                color: viewMode === 'TABLE' ? '#0f172a' : '#64748b',
                fontWeight: 600,
                fontSize: '0.8rem',
                cursor: 'pointer',
                boxShadow: viewMode === 'TABLE' ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
              }}
            >
              Table View
            </button>
            <button
              onClick={() => setViewMode('CARDS')}
              style={{
                padding: '6px 12px',
                borderRadius: 6,
                border: 'none',
                background: viewMode === 'CARDS' ? '#fff' : 'transparent',
                color: viewMode === 'CARDS' ? '#0f172a' : '#64748b',
                fontWeight: 600,
                fontSize: '0.8rem',
                cursor: 'pointer',
                boxShadow: viewMode === 'CARDS' ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
              }}
            >
              Cards View
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0' }}>
          <RefreshCw size={32} className="animate-spin" color="#059669" style={{ margin: '0 auto 16px' }} />
          <p style={{ color: '#64748b', fontSize: '0.95rem' }}>Loading school recommendations...</p>
        </div>
      ) : filteredRecs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0' }}>
          <CheckCircle2 size={40} color="#10b981" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: '#1e293b', marginBottom: 6 }}>
            No Recommendations Found
          </h3>
          <p style={{ color: '#64748b', fontSize: '0.9rem', maxWidth: 450, margin: '0 auto' }}>
            No recommendations match your selected filters. All student support needs have been addressed.
          </p>
        </div>
      ) : viewMode === 'TABLE' ? (
        /* Table View */
        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflowX: 'auto', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '14px 18px' }}>Student</th>
                <th style={{ padding: '14px 18px' }}>Class</th>
                <th style={{ padding: '14px 18px' }}>Risk Assessment</th>
                <th style={{ padding: '14px 18px' }}>Primary Declining Signals</th>
                <th style={{ padding: '14px 18px' }}>Recommended Action</th>
                <th style={{ padding: '14px 18px' }}>Priority</th>
                <th style={{ padding: '14px 18px' }}>Status</th>
                <th style={{ padding: '14px 18px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecs.map((rec) => (
                <tr
                  key={rec.recommendation_id}
                  style={{ borderBottom: '1px solid #f1f5f9', transition: 'background 0.15s' }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = '#fff')}
                >
                  <td style={{ padding: '14px 18px' }}>
                    <div
                      onClick={() => onSelectStudent && onSelectStudent(rec.student_id)}
                      style={{ fontWeight: 600, color: '#0f172a', cursor: onSelectStudent ? 'pointer' : 'default', display: 'flex', alignItems: 'center', gap: 4 }}
                    >
                      {rec.student_name || 'Student'}
                      {onSelectStudent && <ArrowRight size={13} color="#6366f1" />}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>ID: {rec.student_id}</div>
                  </td>

                  <td style={{ padding: '14px 18px' }}>
                    <span style={{ padding: '3px 8px', borderRadius: 6, background: '#f1f5f9', color: '#475569', fontSize: '0.78rem', fontWeight: 600 }}>
                      {rec.class_name || 'Class'}
                    </span>
                  </td>

                  <td style={{ padding: '14px 18px' }}>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: 6,
                        fontWeight: 700,
                        fontSize: '0.78rem',
                        background: (rec.risk_score || 0) >= 60 ? '#fee2e2' : (rec.risk_score || 0) >= 30 ? '#ffedd5' : '#f0fdf4',
                        color: (rec.risk_score || 0) >= 60 ? '#b91c1c' : (rec.risk_score || 0) >= 30 ? '#c2410c' : '#15803d',
                      }}
                    >
                      {rec.risk_level || 'EVAL'} ({rec.risk_score || 0})
                    </span>
                  </td>

                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {rec.signals_summary?.attendance_drop > 0 && (
                          <span style={{ fontSize: '0.72rem', background: '#fee2e2', color: '#991b1b', padding: '1px 6px', borderRadius: 4 }}>
                            Att ↓ {rec.signals_summary.attendance_drop}%
                          </span>
                        )}
                        {rec.signals_summary?.homework_drop > 0 && (
                          <span style={{ fontSize: '0.72rem', background: '#fef3c7', color: '#92400e', padding: '1px 6px', borderRadius: 4 }}>
                            HW ↓ {rec.signals_summary.homework_drop}%
                          </span>
                        )}
                        {rec.signals_summary?.academic_drop > 0 && (
                          <span style={{ fontSize: '0.72rem', background: '#e0e7ff', color: '#3730a3', padding: '1px 6px', borderRadius: 4 }}>
                            Acad ↓ {rec.signals_summary.academic_drop}%
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#64748b', maxWidth: 300, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {rec.explanation}
                      </div>
                    </div>
                  </td>

                  <td style={{ padding: '14px 18px', fontWeight: 600, color: '#0f172a' }}>
                    {rec.recommendation_type.replace(/_/g, ' ')}
                  </td>

                  <td style={{ padding: '14px 18px' }}>
                    {getPriorityBadge(rec.priority_level)}
                  </td>

                  <td style={{ padding: '14px 18px' }}>
                    {rec.status === 'PENDING' && (
                      <span style={{ fontSize: '0.75rem', color: '#d97706', background: '#fef3c7', padding: '3px 8px', borderRadius: 999, fontWeight: 600 }}>
                        Pending
                      </span>
                    )}
                    {rec.status === 'CONVERTED_TO_INTERVENTION' && (
                      <span style={{ fontSize: '0.75rem', color: '#16a34a', background: '#dcfce7', padding: '3px 8px', borderRadius: 999, fontWeight: 600 }}>
                        Approved
                      </span>
                    )}
                    {rec.status === 'DISMISSED' && (
                      <span style={{ fontSize: '0.75rem', color: '#64748b', background: '#f1f5f9', padding: '3px 8px', borderRadius: 999, fontWeight: 600 }}>
                        Dismissed
                      </span>
                    )}
                  </td>

                  <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                      {rec.status === 'PENDING' && (
                        <>
                          <button
                            onClick={() => handleOpenApprove(rec)}
                            style={{
                              padding: '5px 10px',
                              borderRadius: 6,
                              border: 'none',
                              background: '#059669',
                              color: '#fff',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleOpenDismiss(rec)}
                            style={{
                              padding: '5px 8px',
                              borderRadius: 6,
                              border: '1px solid #e2e8f0',
                              background: '#fff',
                              color: '#64748b',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            Dismiss
                          </button>
                        </>
                      )}
                      {onSelectStudent && (
                        <button
                          onClick={() => onSelectStudent(rec.student_id)}
                          style={{
                            padding: '5px 8px',
                            borderRadius: 6,
                            border: '1px solid #cbd5e1',
                            background: '#fff',
                            color: '#334155',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Profile
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        /* Cards View */
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 18 }}>
          {filteredRecs.map((rec) => (
            <div
              key={rec.recommendation_id}
              style={{
                background: '#fff',
                borderRadius: 12,
                border: rec.priority_level === 'URGENT' ? '2px solid #f87171' : '1px solid #e2e8f0',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
                boxShadow: '0 2px 4px rgba(0,0,0,0.04)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4
                    onClick={() => onSelectStudent && onSelectStudent(rec.student_id)}
                    style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0, color: '#0f172a', cursor: onSelectStudent ? 'pointer' : 'default' }}
                  >
                    {rec.student_name || 'Student'}
                  </h4>
                  <span style={{ fontSize: '0.78rem', color: '#64748b' }}>{rec.class_name}</span>
                </div>
                {getPriorityBadge(rec.priority_level)}
              </div>

              <div style={{ background: '#f8fafc', padding: 10, borderRadius: 8, fontSize: '0.85rem' }}>
                <div style={{ fontWeight: 700, color: '#047857', marginBottom: 4 }}>
                  Action: {rec.recommendation_type.replace(/_/g, ' ')}
                </div>
                <p style={{ margin: 0, color: '#475569', fontSize: '0.8rem', lineHeight: 1.4 }}>
                  {rec.explanation}
                </p>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 'auto', paddingTop: 8 }}>
                {rec.status === 'PENDING' && (
                  <>
                    <button
                      onClick={() => handleOpenDismiss(rec)}
                      style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Dismiss
                    </button>
                    <button
                      onClick={() => handleOpenApprove(rec)}
                      style={{ padding: '6px 14px', borderRadius: 6, border: 'none', background: '#059669', color: '#fff', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Approve
                    </button>
                  </>
                )}
                {onSelectStudent && (
                  <button
                    onClick={() => onSelectStudent(rec.student_id)}
                    style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1', background: '#fff', color: '#334155', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
                  >
                    Profile
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Approve Modal */}
      {reviewingRec && (
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
          onClick={() => setReviewingRec(null)}
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
                  Principal Approval — Student Intervention
                </h3>
                <p style={{ fontSize: '0.85rem', color: '#64748b', margin: '4px 0 0' }}>
                  For student: <strong>{reviewingRec.student_name}</strong> ({reviewingRec.class_name})
                </p>
              </div>
              <button onClick={() => setReviewingRec(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: 6 }}>
                  Sanctioned Intervention Type:
                </label>
                <select
                  value={approveType}
                  onChange={(e) => setApproveType(e.target.value as InterventionType)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                >
                  <option value="ONE_ON_ONE_CHECKIN">One-on-One Check-in</option>
                  <option value="ACADEMIC_SUPPORT">Academic Support Clinic</option>
                  <option value="ATTENDANCE_SUPPORT">Attendance Mentorship</option>
                  <option value="EXTRA_ASSIGNMENT">Remedial Assignment</option>
                  <option value="PARENT_CONTACT">Parent Contact Advisory</option>
                  <option value="COUNSELING_REFERRAL">Counseling Referral</option>
                  <option value="FOLLOW_UP_REVIEW">Follow-up Review</option>
                  <option value="OTHER">Other Intervention</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: 6 }}>
                  Directives & Notes:
                </label>
                <textarea
                  rows={4}
                  value={approveNotes}
                  onChange={(e) => setApproveNotes(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: 6 }}>
                  Scheduled Follow-up Date:
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
                onClick={() => setReviewingRec(null)}
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
                  background: '#059669',
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
                Sanction Intervention Plan
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
                  <option value="TEACHER_JUDGMENT">Administrative / Principal Judgment</option>
                  <option value="ISSUE_ALREADY_RESOLVED">Issue Already Resolved</option>
                  <option value="DUPLICATE_RECOMMENDATION">Duplicate Action</option>
                  <option value="NOT_APPLICABLE">Not Applicable</option>
                  <option value="OTHER">Other Reason</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: 6 }}>
                  Optional Administrative Notes:
                </label>
                <textarea
                  rows={3}
                  value={dismissNotes}
                  onChange={(e) => setDismissNotes(e.target.value)}
                  placeholder="Record justification..."
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
