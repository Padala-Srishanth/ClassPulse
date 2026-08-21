import { apiClient } from './client';

export interface IngestionSummary {
  batch_id: string;
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  duplicate_rows: number;
  errors: Array<{ row_number: number; error: string }>;
}

export const ingestionApi = {
  uploadAttendance: (schoolId: string, file: File) => {
    const formData = new FormData();
    formData.append('school_id', schoolId);
    formData.append('file', file);
    return apiClient<IngestionSummary>('/api/v1/ingestion/attendance', {
      method: 'POST',
      body: formData,
    });
  },

  uploadHomework: (schoolId: string, file: File) => {
    const formData = new FormData();
    formData.append('school_id', schoolId);
    formData.append('file', file);
    return apiClient<IngestionSummary>('/api/v1/ingestion/homework', {
      method: 'POST',
      body: formData,
    });
  },

  uploadTestScores: (schoolId: string, file: File) => {
    const formData = new FormData();
    formData.append('school_id', schoolId);
    formData.append('file', file);
    return apiClient<IngestionSummary>('/api/v1/ingestion/test-scores', {
      method: 'POST',
      body: formData,
    });
  },
};
