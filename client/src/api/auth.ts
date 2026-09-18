import { apiFetch } from './client';
import { User } from '../types';

export interface LoginResult {
  token: string;
  user: User & { class_id?: string; student_code?: string };
}

export const authApi = {
  /**
   * Validates credentials against EXISTING data.
   * Username = identifier (student_code / teacher-uid / sadmin-uid-001)
   * Password = same identifier
   * Returns a session token on success.
   */
  login: async (role: string, username: string, password: string): Promise<LoginResult> => {
    const response = await apiFetch('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ role, username, password }),
      headers: {
        Authorization: 'Bearer mock-token',  // unauthenticated public endpoint
      },
    });

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error?.message || 'Login failed. Please check your credentials.');
    }
    return data.data as LoginResult;
  },
};
