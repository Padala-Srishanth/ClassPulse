import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';

interface SubjectPerformanceChartProps {
  subjects: Record<string, {
    tests_count: number;
    average_percentage: number;
    highest_percentage: number;
    lowest_percentage: number;
  }>;
}

export const SubjectPerformanceChart: React.FC<SubjectPerformanceChartProps> = ({ subjects }) => {
  const keys = Object.keys(subjects || {});
  if (keys.length === 0) {
    return (
      <div className="monthly-chart-card" style={{ textAlign: 'center', color: '#64748b', padding: '30px' }}>
        No subject tests recorded for this month.
      </div>
    );
  }

  const data = keys.map((name) => ({
    name,
    average: subjects[name].average_percentage,
    highest: subjects[name].highest_percentage,
    lowest: subjects[name].lowest_percentage,
    count: subjects[name].tests_count,
  }));

  const getBarColor = (val: number) => {
    if (val >= 80) return '#16a34a';
    if (val >= 60) return '#0284c7';
    if (val >= 40) return '#d97706';
    return '#dc2626';
  };

  return (
    <div className="monthly-chart-card">
      <div className="monthly-chart-header">
        <div>
          <h3 className="monthly-chart-title">Subject-Wise Performance Breakdown</h3>
          <p className="monthly-chart-subtitle">Average marks scored across monthly assessments</p>
        </div>
      </div>

      <div style={{ width: '100%', height: '260px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.8} />
            <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#475569', fontSize: 11 }} />
            <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fill: '#475569', fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                borderColor: '#e2e8f0',
                borderRadius: '12px',
                color: '#0f172a',
                fontSize: '12px',
                boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
              }}
              formatter={(val: any, name: any, item: any) => [
                `${Number(val).toFixed(1)}% (${item.payload.count} tests)`,
                'Average Score',
              ]}
            />
            <Bar dataKey="average" radius={[6, 6, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.average)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
