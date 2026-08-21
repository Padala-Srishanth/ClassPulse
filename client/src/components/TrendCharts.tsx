import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { WeeklyEngagementSignature } from '../types';

interface TrendChartsProps {
  signatures: WeeklyEngagementSignature[];
  baselineAttendance?: number | null;
  baselineHomework?: number | null;
  baselineTest?: number | null;
}

export const TrendCharts: React.FC<TrendChartsProps> = ({
  signatures,
  baselineAttendance,
  baselineHomework,
  baselineTest,
}) => {
  if (!signatures || signatures.length === 0) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: '#94a3b8' }}>
        No weekly engagement history recorded yet.
      </div>
    );
  }

  const chartData = signatures.map((s) => ({
    week: s.week_key,
    attendance: s.attendance_rate,
    homework: s.homework_completion_rate,
    testScore: s.average_test_percentage,
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* 1. Attendance Chart */}
      <div className="card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Attendance Trajectory (%)</h4>
            <p style={{ fontSize: '0.78rem', color: '#64748b' }}>Weekly presence rate vs. historical baseline</p>
          </div>
          {baselineAttendance !== undefined && baselineAttendance !== null && (
            <span style={{ fontSize: '0.78rem', color: '#4f46e5', fontWeight: 600, background: '#eef2ff', padding: '4px 10px', borderRadius: '6px' }}>
              Baseline: {baselineAttendance.toFixed(1)}%
            </span>
          )}
        </div>
        <div style={{ width: '100%', height: 200 }}>
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="week" stroke="#94a3b8" fontSize={11} />
              <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
              <Tooltip formatter={(value: any) => [`${value}%`, 'Attendance']} />
              {baselineAttendance && (
                <ReferenceLine y={baselineAttendance} stroke="#6366f1" strokeDasharray="4 4" label="Baseline" />
              )}
              <Line type="monotone" dataKey="attendance" stroke="#4f46e5" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 2. Homework Completion Chart */}
      <div className="card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Homework Completion Rate (%)</h4>
            <p style={{ fontSize: '0.78rem', color: '#64748b' }}>Assignments completed on-time vs. baseline</p>
          </div>
          {baselineHomework !== undefined && baselineHomework !== null && (
            <span style={{ fontSize: '0.78rem', color: '#0891b2', fontWeight: 600, background: '#ecfeff', padding: '4px 10px', borderRadius: '6px' }}>
              Baseline: {baselineHomework.toFixed(1)}%
            </span>
          )}
        </div>
        <div style={{ width: '100%', height: 200 }}>
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="week" stroke="#94a3b8" fontSize={11} />
              <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
              <Tooltip formatter={(value: any) => [`${value}%`, 'Homework Completion']} />
              {baselineHomework && (
                <ReferenceLine y={baselineHomework} stroke="#06b6d4" strokeDasharray="4 4" label="Baseline" />
              )}
              <Line type="monotone" dataKey="homework" stroke="#0891b2" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. Test Scores Chart */}
      <div className="card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Test Score Average (%)</h4>
            <p style={{ fontSize: '0.78rem', color: '#64748b' }}>Assessment results across weeks</p>
          </div>
          {baselineTest !== undefined && baselineTest !== null && (
            <span style={{ fontSize: '0.78rem', color: '#8b5cf6', fontWeight: 600, background: '#f5f3ff', padding: '4px 10px', borderRadius: '6px' }}>
              Baseline: {baselineTest.toFixed(1)}%
            </span>
          )}
        </div>
        <div style={{ width: '100%', height: 200 }}>
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="week" stroke="#94a3b8" fontSize={11} />
              <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
              <Tooltip formatter={(value: any) => [value ? `${value}%` : 'No test', 'Test Average']} />
              {baselineTest && (
                <ReferenceLine y={baselineTest} stroke="#8b5cf6" strokeDasharray="4 4" label="Baseline" />
              )}
              <Line type="monotone" dataKey="testScore" stroke="#7c3aed" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
