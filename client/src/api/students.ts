import { apiClient } from './client';
import { Student } from '../types';

export const studentsApi = {
  listClassStudents: (classId: string) =>
    apiClient<Student[]>(`/api/v1/students/class/${classId}`),

  getStudent: (studentId: string) =>
    apiClient<Student>(`/api/v1/students/${studentId}`),

  createStudent: (data: Partial<Student>) =>
    apiClient<Student>('/api/v1/students', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateStudent: (studentId: string, data: Partial<Student>) =>
    apiClient<Student>(`/api/v1/students/${studentId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
};

