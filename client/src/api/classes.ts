import { apiClient } from './client';
import { SchoolClass } from '../types';

export const classesApi = {
  listSchoolClasses: (schoolId: string) =>
    apiClient<SchoolClass[]>(`/api/v1/classes/school/${schoolId}`),

  getClass: (classId: string) =>
    apiClient<SchoolClass>(`/api/v1/classes/${classId}`),

  createClass: (data: Partial<SchoolClass>) =>
    apiClient<SchoolClass>('/api/v1/classes', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  recordClassAttendance: (classId: string, date: string, records: Array<{ student_id: string; status: string }>) =>
    apiClient<{ recorded_count: number; date: string; class_id: string }>(`/api/v1/classes/${classId}/attendance`, {
      method: 'POST',
      body: JSON.stringify({ date, records }),
    }),
};

