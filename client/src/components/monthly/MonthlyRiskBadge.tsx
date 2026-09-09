import React from 'react';
import { AlertTriangle, CheckCircle2, HelpCircle, ShieldAlert, ShieldCheck } from 'lucide-react';

interface MonthlyRiskBadgeProps {
  level: string;
  score?: number | null;
  size?: 'sm' | 'md' | 'lg';
}

export const MonthlyRiskBadge: React.FC<MonthlyRiskBadgeProps> = ({
  level,
  score,
  size = 'md',
}) => {
  const norm = (level || '').toUpperCase();

  let bg = '#f1f5f9';
  let border = '#cbd5e1';
  let text = '#475569';
  let icon = <HelpCircle size={14} color="#64748b" />;
  let label = 'No Data';

  if (norm === 'HIGH') {
    bg = '#fff1f2';
    border = '#fecdd3';
    text = '#be123c';
    icon = <ShieldAlert size={14} color="#e11d48" />;
    label = 'High Risk';
  } else if (norm === 'MEDIUM') {
    bg = '#fffbeb';
    border = '#fde68a';
    text = '#b45309';
    icon = <AlertTriangle size={14} color="#f59e0b" />;
    label = 'Medium Risk';
  } else if (norm === 'LOW') {
    bg = '#f0fdf4';
    border = '#bbf7d0';
    text = '#15803d';
    icon = <ShieldCheck size={14} color="#16a34a" />;
    label = 'Low Risk';
  } else if (norm === 'INSUFFICIENT_DATA') {
    bg = '#eff6ff';
    border = '#bfdbfe';
    text = '#1d4ed8';
    icon = <HelpCircle size={14} color="#3b82f6" />;
    label = 'Needs Data';
  }

  const padding = size === 'sm' ? '3px 10px' : size === 'lg' ? '8px 18px' : '5px 14px';
  const fontSize = size === 'sm' ? '0.75rem' : size === 'lg' ? '0.95rem' : '0.825rem';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        backgroundColor: bg,
        border: `1px solid ${border}`,
        color: text,
        borderRadius: '9999px',
        padding,
        fontSize,
        fontWeight: 700,
        boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
      }}
    >
      {icon}
      <span>{label}</span>
      {score !== undefined && score !== null && (
        <span style={{ opacity: 0.85, fontFamily: 'monospace', fontWeight: 800 }}>
          ({score.toFixed(1)})
        </span>
      )}
    </span>
  );
};
