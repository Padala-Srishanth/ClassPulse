import { apiClient } from './client';
import { Intervention } from '../types';

export const interventionsApi = {
  createIntervention: (data: {
    student_id: string;
    school_id: string;
    class_id: string;
    type: string;
    notes: string;
    follow_up_date?: string;
  }) =>
    apiClient<Intervention>('/api/v1/interventions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateIntervention: (id: string, data: Partial<Intervention>) =>
    apiClient<Intervention>(`/api/v1/interventions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  listStudentInterventions: (studentId: string) =>
    apiClient<Intervention[]>(`/api/v1/interventions/student/${studentId}`),

  listClassInterventions: (classId: string) =>
    apiClient<Intervention[]>(`/api/v1/interventions/class/${classId}`),

  listSchoolInterventions: (schoolId: string) =>
    apiClient<Intervention[]>(`/api/v1/interventions/school/${schoolId}`),
};
