import React from 'react';
import { LucideIcon } from 'lucide-react';

interface RiskCardProps {
  title: string;
  count: number;
  subtitle?: string;
  icon: LucideIcon;
  colorClass: string;
  bgLight: string;
  textColor: string;
}

export const RiskCard: React.FC<RiskCardProps> = ({
  title,
  count,
  subtitle,
  icon: Icon,
  bgLight,
  textColor,
}) => {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ backgroundColor: bgLight, color: textColor }}>
        <Icon size={24} />
      </div>
      <div>
        <p style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          {title}
        </p>
        <h3 style={{ fontSize: '1.6rem', fontWeight: 700, color: '#0f172a', margin: '2px 0' }}>
          {count}
        </h3>
        {subtitle && <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{subtitle}</p>}
      </div>
    </div>
  );
};
