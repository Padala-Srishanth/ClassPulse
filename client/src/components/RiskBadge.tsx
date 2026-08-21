import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, HelpCircle } from 'lucide-react';
import { RiskLevel } from '../types';

interface RiskBadgeProps {
  level: RiskLevel;
  score?: number;
  showScore?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, score, showScore = true }) => {
  switch (level) {
    case 'HIGH':
      return (
        <span className="badge badge-high" title={`High Risk${score !== undefined ? `: ${score}` : ''}`}>
          <AlertCircle size={13} aria-hidden="true" />
          High Risk {showScore && score !== undefined ? `(${score})` : ''}
        </span>
      );
    case 'MEDIUM':
      return (
        <span className="badge badge-medium" title={`Medium Risk${score !== undefined ? `: ${score}` : ''}`}>
          <AlertTriangle size={13} aria-hidden="true" />
          Medium Risk {showScore && score !== undefined ? `(${score})` : ''}
        </span>
      );
    case 'LOW':
      return (
        <span className="badge badge-low" title={`Low Risk${score !== undefined ? `: ${score}` : ''}`}>
          <CheckCircle2 size={13} aria-hidden="true" />
          Stable {showScore && score !== undefined ? `(${score})` : ''}
        </span>
      );
    case 'INSUFFICIENT_DATA':
    default:
      return (
        <span className="badge badge-na" title="Insufficient historical data">
          <HelpCircle size={13} aria-hidden="true" />
          Needs Data
        </span>
      );
  }
};
