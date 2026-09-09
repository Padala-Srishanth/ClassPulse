/**
 * client/src/api/monthly_reports.ts — API Client for Monthly Reports & Historical Risk
 */

import { apiClient } from './client';
import {
  MonthlyClassReport,
  MonthlySchoolReport,
  MonthlyStudentReport,
} from '../types';

export async function getReportingPeriods(): Promise<string[]> {
  const data = await apiClient<{ periods: string[] }>('/api/v1/monthly-reports/periods');
  return data.periods;
}

export async function getStudentMonthlyReport(
  studentId: string,
  reportPeriod: string
): Promise<MonthlyStudentReport> {
  return apiClient<MonthlyStudentReport>(
    `/api/v1/monthly-reports/student/${studentId}?report_period=${reportPeriod}`
  );
}

export async function getStudentMonthlyHistory(
  studentId: string
): Promise<MonthlyStudentReport[]> {
  const data = await apiClient<{ history: MonthlyStudentReport[]; count: number }>(
    `/api/v1/monthly-reports/student/${studentId}/history`
  );
  return data.history;
}

export async function generateStudentMonthlyReport(
  studentId: string,
  reportPeriod: string
): Promise<MonthlyStudentReport> {
  return apiClient<MonthlyStudentReport>(
    `/api/v1/monthly-reports/generate/student/${studentId}`,
    {
      method: 'POST',
      body: JSON.stringify({ report_period: reportPeriod }),
    }
  );
}

export async function getClassMonthlyReport(
  classId: string,
  reportPeriod: string
): Promise<MonthlyClassReport> {
  return apiClient<MonthlyClassReport>(
    `/api/v1/monthly-reports/class/${classId}?report_period=${reportPeriod}`
  );
}

export async function generateClassMonthlyReport(
  classId: string,
  reportPeriod: string
): Promise<MonthlyClassReport> {
  return apiClient<MonthlyClassReport>(
    `/api/v1/monthly-reports/generate/class/${classId}`,
    {
      method: 'POST',
      body: JSON.stringify({ report_period: reportPeriod }),
    }
  );
}

export async function getSchoolMonthlyReport(
  schoolId: string,
  reportPeriod: string
): Promise<MonthlySchoolReport> {
  return apiClient<MonthlySchoolReport>(
    `/api/v1/monthly-reports/school/${schoolId}?report_period=${reportPeriod}`
  );
}

export async function generateSchoolMonthlyReport(
  schoolId: string,
  reportPeriod: string
): Promise<MonthlySchoolReport> {
  return apiClient<MonthlySchoolReport>(
    `/api/v1/monthly-reports/generate/school/${schoolId}`,
    {
      method: 'POST',
      body: JSON.stringify({ report_period: reportPeriod }),
    }
  );
}
