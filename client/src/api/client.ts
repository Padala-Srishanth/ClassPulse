const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    request_id: string;
    timestamp: string;
  };
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Retrieve token from demo user storage or auth
  const savedDemo = localStorage.getItem('classpulse_demo_user');
  let token = 'mock-teacher-token';
  if (savedDemo) {
    try {
      token = JSON.parse(savedDemo).token || token;
    } catch (e) {
      // ignore
    }
  }

  if (!headers.has('Authorization') && token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const baseUrlClean = BASE_URL.trim().replace(/\/+$/, '');
  const endpointClean = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = endpoint.startsWith('http') ? endpoint : `${baseUrlClean}${endpointClean}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const json: ApiResponse<T> = await response.json();

  if (!response.ok || !json.success) {
    let errorMsg = json.error?.message || `Request failed with status ${response.status}`;
    if (json.error?.details && Array.isArray(json.error.details) && json.error.details.length > 0) {
      const detailStr = json.error.details
        .map((d: any) => `${d.loc ? d.loc.filter((l: string) => l !== 'body').join('.') + ': ' : ''}${d.msg}`)
        .join('; ');
      errorMsg = `${errorMsg} (${detailStr})`;
    }
    throw new Error(errorMsg);
  }

  return json.data;
}
