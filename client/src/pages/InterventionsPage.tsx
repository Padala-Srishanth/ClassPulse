import React, { useEffect, useState } from 'react';
import { Calendar, CheckCircle2, Clock, Filter, GraduationCap, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { interventionsApi } from '../api/interventions';
import { Intervention } from '../types';

export const InterventionsPage: React.FC = () => {
  const { schoolId } = useAuth();
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  const loadInterventions = async () => {
    if (!schoolId) return;
    setLoading(true);
    try {
      const data = await interventionsApi.listSchoolInterventions(schoolId);
      setInterventions(data);
    } catch (err) {
      console.error('Error fetching interventions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInterventions();
  }, [schoolId]);

  const filtered = interventions.filter((item) => {
    if (filterStatus === 'ALL') return true;
    return item.status === filterStatus;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Teacher Interventions Hub</h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Monitor and track follow-ups, remedial actions, and student outcome progression.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} color="#64748b" />
          <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#475569' }}>Status:</span>
          {['ALL', 'PLANNED', 'IN_PROGRESS', 'COMPLETED'].map((st) => (
            <button
              key={st}
              className={`btn btn-sm ${filterStatus === st ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setFilterStatus(st)}
            >
              {st.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="table-container">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
            Loading school interventions...
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
            No interventions recorded matching current filter.
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Action Notes</th>
                <th>Follow-up</th>
                <th>Status</th>
                <th>Recorded Outcome</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => {
                const isCompleted = item.status === 'COMPLETED';
                return (
                  <tr key={item.id}>
                    <td style={{ fontSize: '0.82rem', color: '#64748b', whiteSpace: 'nowrap' }}>
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: '6px',
                          background: '#f1f5f9',
                          color: '#334155',
                          textTransform: 'uppercase',
                        }}
                      >
                        {item.type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.88rem', color: '#1e293b', maxWidth: '350px' }}>
                      {item.notes}
                    </td>
                    <td style={{ fontSize: '0.82rem', color: '#64748b', whiteSpace: 'nowrap' }}>
                      {item.follow_up_date || 'None'}
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: '6px',
                          background: isCompleted ? '#d1fae5' : '#e0e7ff',
                          color: isCompleted ? '#065f46' : '#3730a3',
                          textTransform: 'uppercase',
                        }}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem' }}>
                      {item.outcome ? (
                        <span style={{ color: '#15803d', fontWeight: 600 }}>
                          {item.outcome.replace(/_/g, ' ')}
                        </span>
                      ) : (
                        <span style={{ color: '#94a3b8' }}>Pending</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
