import React from 'react';
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';
import { TrendDirection } from '../../types';

interface MonthlyTrendBadgeProps {
  delta: number | null;
  direction: TrendDirection;
  unit?: string;
  inverse?: boolean;
}

export const MonthlyTrendBadge: React.FC<MonthlyTrendBadgeProps> = ({
  delta,
  direction,
  unit = '%',
  inverse = false,
}) => {
  if (direction === 'INSUFFICIENT_HISTORY' || delta === null || delta === undefined) {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '0.7rem',
          fontWeight: 600,
          color: '#64748b',
          backgroundColor: '#f1f5f9',
          padding: '2px 8px',
          borderRadius: '6px',
          border: '1px solid #e2e8f0',
        }}
      >
        <Minus size={12} />
        <span>First Month</span>
      </span>
    );
  }

  const isImproving = direction === 'IMPROVING';
  const isDeclining = direction === 'DECLINING';

  let bg = '#f8fafc';
  let border = '#e2e8f0';
  let text = '#475569';
  let Icon = Minus;

  if (isImproving) {
    bg = '#f0fdf4';
    border = '#bbf7d0';
    text = '#15803d';
    Icon = TrendingUp;
  } else if (isDeclining) {
    bg = '#fff1f2';
    border = '#fecdd3';
    text = '#be123c';
    Icon = TrendingDown;
  }

  const sign = delta > 0 ? '+' : '';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        fontSize: '0.7rem',
        fontWeight: 700,
        backgroundColor: bg,
        border: `1px solid ${border}`,
        color: text,
        padding: '2px 8px',
        borderRadius: '6px',
      }}
    >
      <Icon size={13} />
      <span>
        {sign}{delta.toFixed(1)}{unit} MoM
      </span>
    </span>
  );
};
