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

const DEFAULT_TIMEOUT_MS = 10000;

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
      const err = jsonPayload as { error?: APIErrorDetail };
      throw new APIClientError({
        code: err?.error?.code ?? `HTTP_${response.status}`,
        message: err?.error?.message ?? "An error occurred while communicating with the server.",
        request_id: err?.error?.request_id ?? responseRequestId,
        details: err?.error?.details,
      });
    }

    return jsonPayload as APIResponse<T>;
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
