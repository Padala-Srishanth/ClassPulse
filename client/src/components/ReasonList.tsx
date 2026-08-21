import React from 'react';
import { AlertCircle, ArrowDownRight, Clock, HelpCircle, Layers } from 'lucide-react';
import { SignalReason } from '../types';

interface ReasonListProps {
  reasons: SignalReason[];
}

export const ReasonList: React.FC<ReasonListProps> = ({ reasons }) => {
  if (!reasons || reasons.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>
        No explicit risk indicators detected. Student performance is stable within baseline.
      </div>
    );
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'ATTENDANCE_DECLINE':
      case 'HOMEWORK_DECLINE':
      case 'TEST_SCORE_DECLINE':
        return <ArrowDownRight size={18} />;
      case 'PERSISTENT_DECLINE':
        return <Clock size={18} />;
      case 'MULTI_SIGNAL_AGREEMENT':
        return <Layers size={18} />;
      case 'INSUFFICIENT_HISTORY':
        return <HelpCircle size={18} />;
      default:
        return <AlertCircle size={18} />;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {reasons.map((reason, idx) => {
        const isHigh = reason.severity === 'HIGH';
        const isMed = reason.severity === 'MEDIUM';
        const cardClass = isHigh ? 'reason-card sev-high' : (isMed ? 'reason-card sev-medium' : 'reason-card');

        return (
          <div key={idx} className={cardClass}>
            <div style={{ color: isHigh ? '#e11d48' : (isMed ? '#d97706' : '#4f46e5'), marginTop: '2px' }}>
              {getIcon(reason.signal_type)}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#0f172a' }}>
                  {reason.explanation}
                </span>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '9999px',
                    background: isHigh ? '#ffe4e6' : (isMed ? '#fef3c7' : '#e0e7ff'),
                    color: isHigh ? '#be123c' : (isMed ? '#92400e' : '#3730a3'),
                    textTransform: 'uppercase',
                  }}
                >
                  {reason.severity}
                </span>
              </div>

              {reason.baseline_value > 0 && reason.metric !== 'total_weeks' && (
                <div style={{ display: 'flex', gap: '18px', fontSize: '0.78rem', color: '#64748b', marginTop: '6px' }}>
                  <span>
                    <strong>Historical Baseline:</strong> {reason.baseline_value.toFixed(1)}%
                  </span>
                  <span>
                    <strong>Recent Evaluation:</strong> {reason.current_value.toFixed(1)}%
                  </span>
                  <span style={{ color: reason.change < 0 ? '#e11d48' : '#15803d', fontWeight: 600 }}>
                    <strong>Delta:</strong> {reason.change > 0 ? `+${reason.change.toFixed(1)}%` : `${reason.change.toFixed(1)}%`}
                  </span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
