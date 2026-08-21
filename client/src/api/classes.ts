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
};
