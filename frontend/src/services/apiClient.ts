/**
 * Resilient API client with timeout protection, error normalization, and request correlation.
 */

import { APIResponse, APIErrorDetail } from "../types/api.ts";

export class APIClientError extends Error {
  public readonly code: string;
  public readonly requestId?: string;
  public readonly details?: unknown;

  constructor(error: APIErrorDetail) {
    super(error.message);
    this.name = "APIClientError";
    this.code = error.code;
    this.requestId = error.request_id;
    this.details = error.details;
  }
}

let inMemoryAccessToken: string | null = null;
try {
  inMemoryAccessToken = localStorage.getItem("dsaapp_access_token");
} catch {}

let inMemoryRefreshToken: string | null = null;
try {
  inMemoryRefreshToken = localStorage.getItem("dsaapp_refresh_token");
} catch {}

export function setAccessToken(token: string | null): void {
  inMemoryAccessToken = token;
  try {
    if (token) {
      localStorage.setItem("dsaapp_access_token", token);
    } else {
      localStorage.removeItem("dsaapp_access_token");
    }
  } catch {}
}

export function getAccessToken(): string | null {
  if (!inMemoryAccessToken) {
    try {
      inMemoryAccessToken = localStorage.getItem("dsaapp_access_token");
    } catch {}
  }
  return inMemoryAccessToken;
}

export function setRefreshToken(token: string | null): void {
  inMemoryRefreshToken = token;
  try {
    if (token) {
      localStorage.setItem("dsaapp_refresh_token", token);
    } else {
      localStorage.removeItem("dsaapp_refresh_token");
    }
  } catch {}
}

export function getRefreshToken(): string | null {
  if (!inMemoryRefreshToken) {
    try {
      inMemoryRefreshToken = localStorage.getItem("dsaapp_refresh_token");
    } catch {}
  }
  return inMemoryRefreshToken;
}

const DEFAULT_TIMEOUT_MS = 10000;
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

async function attemptTokenRefresh(): Promise<string | null> {
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }
  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const storedRefresh = getRefreshToken();
      const headers: Record<string, string> = { Accept: "application/json" };
      let body: string | undefined = undefined;
      if (storedRefresh) {
        headers["Content-Type"] = "application/json";
        body = JSON.stringify({ refresh_token: storedRefresh });
      }

      const res = await fetch("/api/v1/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers,
        body,
      });

      if (!res.ok) {
        setAccessToken(null);
        setRefreshToken(null);
        return null;
      }

      const data = await res.json();
      const newAccess = data?.data?.access_token;
      const newRefresh = data?.data?.refresh_token;
      if (newAccess) {
        setAccessToken(newAccess);
        if (newRefresh) setRefreshToken(newRefresh);
        return newAccess;
      }
      return null;
    } catch {
      setAccessToken(null);
      setRefreshToken(null);
      return null;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<APIResponse<T>> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (inMemoryAccessToken && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${inMemoryAccessToken}`;
  }

  if (options.body && typeof options.body === "string" && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const response = await fetch(endpoint, {
      credentials: options.credentials ?? "include",
      ...options,
      headers,
      signal: controller.signal,
    });

    const responseRequestId = response.headers.get("x-request-id") ?? undefined;
    let jsonPayload: unknown;

    try {
      jsonPayload = await response.json();
    } catch {
      throw new APIClientError({
        code: `HTTP_${response.status}`,
        message: response.statusText || "Malformed server response",
        request_id: responseRequestId,
      });
    }

    if (!response.ok) {
      // Automatic transparent token refresh and retry on 401 Unauthorized
      if (response.status === 401 && !endpoint.includes("/api/v1/auth/")) {
        const refreshedToken = await attemptTokenRefresh();
        if (refreshedToken) {
          const retryHeaders = {
            ...headers,
            Authorization: `Bearer ${refreshedToken}`,
          };
          const retryResp = await fetch(endpoint, {
            credentials: options.credentials ?? "include",
            ...options,
            headers: retryHeaders,
            signal: controller.signal,
          });
          if (retryResp.ok) {
            const retryJson = await retryResp.json();
            const retryPayload = retryJson as any;
            if (retryPayload && typeof retryPayload === "object" && "data" in retryPayload && retryPayload.data !== undefined) {
              return retryPayload as APIResponse<T>;
            }
            return {
              success: true,
              data: retryPayload as T,
              request_id: retryResp.headers.get("x-request-id") ?? undefined,
            };
          }
        }
      }

      const err = jsonPayload as { error?: APIErrorDetail };
      throw new APIClientError({
        code: err?.error?.code ?? `HTTP_${response.status}`,
        message: err?.error?.message ?? "An error occurred while communicating with the server.",
        request_id: err?.error?.request_id ?? responseRequestId,
        details: err?.error?.details,
      });
    }

    const payload = jsonPayload as any;
    if (payload && typeof payload === "object" && "data" in payload && payload.data !== undefined) {
      return payload as APIResponse<T>;
    }
    return {
      success: true,
      data: payload as T,
      request_id: responseRequestId,
    };
  } catch (error: unknown) {
    if (error instanceof APIClientError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new APIClientError({
        code: "TIMEOUT",
        message: "The server took too long to respond. Please check your connection and retry.",
      });
    }
    throw new APIClientError({
      code: "NETWORK_ERROR",
      message: "Unable to reach server. Please ensure the backend is running.",
    });
  } finally {
    clearTimeout(timeoutId);
  }
}
