import { apiClient } from './client';
import {
  InterventionRecommendation,
  RecommendationApprovePayload,
  RecommendationDismissPayload,
} from '../types';

export const recommendationsApi = {
  analyzeStudent: (studentId: string) =>
    apiClient<InterventionRecommendation[]>(
      `/api/v1/intervention-recommendations/student/${studentId}/analyze`,
      { method: 'POST' }
    ),

  getStudentRecommendations: (studentId: string, status?: string) =>
    apiClient<InterventionRecommendation[]>(
      `/api/v1/intervention-recommendations/student/${studentId}${status ? `?status=${status}` : ''}`
    ),

  getClassRecommendations: (classId: string) =>
    apiClient<InterventionRecommendation[]>(
      `/api/v1/intervention-recommendations/class/${classId}`
    ),

  getSchoolRecommendations: (schoolId: string, status?: string) =>
    apiClient<InterventionRecommendation[]>(
      `/api/v1/intervention-recommendations/school/${schoolId}${status ? `?status=${status}` : ''}`
    ),

  approveRecommendation: (
    recommendationId: string,
    payload?: RecommendationApprovePayload
  ) =>
    apiClient<{ recommendation: InterventionRecommendation; intervention_id: string }>(
      `/api/v1/intervention-recommendations/${recommendationId}/approve`,
      {
        method: 'POST',
        body: payload ? JSON.stringify(payload) : undefined,
      }
    ),

  dismissRecommendation: (
    recommendationId: string,
    payload: RecommendationDismissPayload
  ) =>
    apiClient<InterventionRecommendation>(
      `/api/v1/intervention-recommendations/${recommendationId}/dismiss`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    ),
};
