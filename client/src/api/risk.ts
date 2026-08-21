import { apiClient } from './client';
import { ClassRiskSummary, RiskAlert, StudentRiskAnalysis } from '../types';

export const riskApi = {
  analyzeStudent: (studentId: string) =>
    apiClient<StudentRiskAnalysis>(`/api/v1/risk/analyze/student/${studentId}`, {
      method: 'POST',
    }),

  analyzeClass: (classId: string) =>
    apiClient<ClassRiskSummary>(`/api/v1/risk/analyze/class/${classId}`, {
      method: 'POST',
    }),

  getStudentLatestAlert: (studentId: string) =>
    apiClient<RiskAlert>(`/api/v1/risk/students/${studentId}/latest`),

  getStudentRiskHistory: (studentId: string) =>
    apiClient<RiskAlert[]>(`/api/v1/risk/students/${studentId}/history`),

  getClassActiveAlerts: (classId: string) =>
    apiClient<RiskAlert[]>(`/api/v1/risk/classes/${classId}/latest`),
};
