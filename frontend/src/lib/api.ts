import { ReflectionRequest, ReflectionResponse } from '@/types/api';

const API_BASE = '/api';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function generateReflection(request: ReflectionRequest, mock: boolean = false): Promise<ReflectionResponse> {
  const url = new URL(`${API_BASE}/reflections`, window.location.origin);
  if (mock) {
    url.searchParams.set('mock', 'true');
  }
  
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let errorMessage = 'Failed to generate reflection';
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // If we can't parse the error response, use the status text
      errorMessage = response.statusText || errorMessage;
    }
    throw new ApiError(response.status, errorMessage);
  }

  return response.json();
}