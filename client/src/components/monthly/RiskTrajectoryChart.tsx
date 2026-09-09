import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceArea,
} from 'recharts';
import { MonthlyStudentReport } from '../../types';

interface RiskTrajectoryChartProps {
  history: MonthlyStudentReport[];
}

const formatMonthLabel = (period: string) => {
  if (!period) return '';
  const [, month] = period.split('-');
  const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const idx = parseInt(month, 10) - 1;
  return names[idx] || period;
};

export const RiskTrajectoryChart: React.FC<RiskTrajectoryChartProps> = ({ history }) => {
  if (!history || history.length === 0) {
    return (
      <div className="monthly-chart-card" style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
        No historical records found for this cohort.
      </div>
    );
  }

  const data = history.map((item) => ({
    period: item.report_period,
    label: formatMonthLabel(item.report_period),
    attendance: item.attendance.attendance_percentage,
    homework: item.homework.completion_rate,
    academic: item.academic.average_percentage,
    risk: item.risk.risk_score,
  }));

  return (
    <div className="monthly-chart-card">
      <div className="monthly-chart-header">
        <div>
          <h3 className="monthly-chart-title">
            6-Month Historical Trajectory & Risk Evolution
          </h3>
          <p className="monthly-chart-subtitle">
            Longitudinal trend of Attendance, Homework, Academic test averages, and drop-based Risk Score
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.75rem', color: '#64748b' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#bbf7d0', border: '1px solid #16a34a' }} />
            <span>Low Risk (&lt;20)</span>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#fde68a', border: '1px solid #f59e0b' }} />
            <span>Med Risk (20-50)</span>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#fecdd3', border: '1px solid #e11d48' }} />
            <span>High Risk (&gt;50)</span>
          </span>
        </div>
      </div>

      <div style={{ width: '100%', height: '320px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.8} />

            <ReferenceArea y1={0} y2={20} fill="#10b981" fillOpacity={0.06} />
            <ReferenceArea y1={20} y2={50} fill="#f59e0b" fillOpacity={0.06} />
            <ReferenceArea y1={50} y2={100} fill="#ef4444" fillOpacity={0.08} />

            <XAxis dataKey="label" stroke="#64748b" tick={{ fill: '#475569', fontSize: 12 }} />
            <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fill: '#475569', fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                borderColor: '#e2e8f0',
                borderRadius: '12px',
                color: '#0f172a',
                fontSize: '12px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
              }}
              formatter={(value: any, name: any) => {
                if (value === null || value === undefined) return ['N/A', name];
                return [`${Number(value).toFixed(1)}%`, name];
              }}
            />
            <Legend wrapperStyle={{ paddingTop: '14px', fontSize: '12px' }} />

            <Line
              type="monotone"
              dataKey="attendance"
              name="Attendance Rate"
              stroke="#0284c7"
              strokeWidth={2.5}
              dot={{ r: 4, fill: '#0284c7' }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="homework"
              name="Homework Completion"
              stroke="#7c3aed"
              strokeWidth={2.5}
              dot={{ r: 4, fill: '#7c3aed' }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="academic"
              name="Academic Marks Avg"
              stroke="#16a34a"
              strokeWidth={2.5}
              dot={{ r: 4, fill: '#16a34a' }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="risk"
              name="Drop Risk Score"
              stroke="#dc2626"
              strokeWidth={3}
              strokeDasharray="4 2"
              dot={{ r: 5, fill: '#dc2626' }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
