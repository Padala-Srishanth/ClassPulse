import React from 'react';
import { Calendar } from 'lucide-react';

interface MonthlyPeriodSelectorProps {
  periods: string[];
  selectedPeriod: string;
  onChange: (period: string) => void;
  isLoading?: boolean;
}

const formatPeriod = (p: string) => {
  if (!p) return '';
  const [year, month] = p.split('-');
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
  const mIdx = parseInt(month, 10) - 1;
  return `${monthNames[mIdx] || month} ${year}`;
};

export const MonthlyPeriodSelector: React.FC<MonthlyPeriodSelectorProps> = ({
  periods,
  selectedPeriod,
  onChange,
  isLoading = false,
}) => {
  return (
    <div className="monthly-selector-box">
      <Calendar size={18} color="#818cf8" />
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8' }}>
          Report Period
        </span>
        <select
          value={selectedPeriod}
          onChange={(e) => onChange(e.target.value)}
          disabled={isLoading}
        >
          {periods.map((p) => (
            <option key={p} value={p}>
              {formatPeriod(p)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};
