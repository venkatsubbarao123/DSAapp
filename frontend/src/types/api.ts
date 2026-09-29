/**
 * Uniform API Contract interfaces matching backend response envelopes.
 */

export interface APIResponse<T> {
  success: boolean;
  data: T;
  request_id?: string;
}

export interface APIErrorDetail {
  code: string;
  message: string;
  request_id?: string;
  details?: unknown;
}

export interface APIErrorResponse {
  success: false;
  error: APIErrorDetail;
}

export interface HealthData {
  status: "healthy" | "degraded";
  service: string;
  environment: string;
  database: "connected" | "disconnected";
  redis: string;
}
