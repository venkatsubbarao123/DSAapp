/**
 * Resilient API client with timeout protection, error normalization,
 * authentication refresh, and cache protection.
 */

import { APIResponse, APIErrorDetail } from "../types/api.ts";

/**
 * Base URL for all backend API calls.
 *
 * Local development:
 *   Vite proxy handles /api and /health.
 *
 * Production:
 *   VITE_API_BASE_URL points to the Railway backend.
 */
export const API_BASE_URL: string = (
  (import.meta.env?.VITE_API_BASE_URL as string | undefined) ?? ""
).replace(/\/+$/, "");

export function apiUrl(path: string): string {
  if (!path.startsWith("/")) {
    throw new Error(
      `apiUrl expects an absolute path starting with '/', got '${path}'`
    );
  }

  return `${API_BASE_URL}${path}`;
}

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

/**
 * AI requests need a longer timeout because third-party LLM
 * providers can take considerably longer than normal API requests.
 */
export const AI_REQUEST_TIMEOUT_MS = 90000;

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

/**
 * Headers used to prevent browser/proxy caching.
 */
const NO_CACHE_HEADERS: Record<string, string> = {
  "Cache-Control": "no-cache, no-store, must-revalidate",
  Pragma: "no-cache",
  Expires: "0",
};

/**
 * Add a cache-busting query parameter.
 *
 * This is intentionally used for GET requests so that even if
 * a browser, CDN, reverse proxy, or Railway layer attempts to
 * return a cached 304 response, the URL is unique.
 */
function addCacheBuster(url: string): string {
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}_cb=${Date.now()}_${Math.random()
    .toString(36)
    .slice(2)}`;
}

/**
 * Refresh access token.
 */
async function attemptTokenRefresh(): Promise<string | null> {
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;

  refreshPromise = (async () => {
    try {
      const storedRefresh = getRefreshToken();

      const headers: Record<string, string> = {
        Accept: "application/json",
        ...NO_CACHE_HEADERS,
      };

      let body: string | undefined;

      if (storedRefresh) {
        headers["Content-Type"] = "application/json";

        body = JSON.stringify({
          refresh_token: storedRefresh,
        });
      }

      const refreshUrl = addCacheBuster(
        apiUrl("/api/v1/auth/refresh")
      );

      const response = await fetch(refreshUrl, {
        method: "POST",
        credentials: "include",
        headers,
        body,
        cache: "no-store",
      });

      if (!response.ok) {
        setAccessToken(null);
        setRefreshToken(null);
        return null;
      }

      const data = await response.json();

      const newAccess = data?.data?.access_token;
      const newRefresh = data?.data?.refresh_token;

      if (newAccess) {
        setAccessToken(newAccess);

        if (newRefresh) {
          setRefreshToken(newRefresh);
        }

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

/**
 * Main API request function.
 */
export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<APIResponse<T>> {
  const controller = new AbortController();

  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...NO_CACHE_HEADERS,
    ...(options.headers as Record<string, string>),
  };

  if (inMemoryAccessToken && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${inMemoryAccessToken}`;
  }

  if (
    options.body &&
    typeof options.body === "string" &&
    !headers["Content-Type"]
  ) {
    headers["Content-Type"] = "application/json";
  }

  const originalTarget = apiUrl(endpoint);

  /**
   * Add cache-buster only to GET/HEAD requests.
   *
   * POST/PUT/PATCH/DELETE requests must not have their URLs
   * unnecessarily modified.
   */
  const method = (options.method ?? "GET").toUpperCase();

  const target =
    method === "GET" || method === "HEAD"
      ? addCacheBuster(originalTarget)
      : originalTarget;

  try {
    const response = await fetch(target, {
      ...options,
      method,
      credentials: options.credentials ?? "include",
      headers,
      signal: controller.signal,
      cache: "no-store",
    });

    const responseRequestId =
      response.headers.get("x-request-id") ?? undefined;

    /**
     * Normally cache-busting prevents 304.
     *
     * If a proxy still returns 304, make one additional request
     * using a fresh unique URL.
     */
    if (response.status === 304) {
      const retryTarget = addCacheBuster(originalTarget);

      const retryResponse = await fetch(retryTarget, {
        ...options,
        method,
        credentials: options.credentials ?? "include",
        headers: {
          ...headers,
          ...NO_CACHE_HEADERS,
        },
        signal: controller.signal,
        cache: "no-store",
      });

      if (!retryResponse.ok) {
        throw new APIClientError({
          code: `HTTP_${retryResponse.status}`,
          message:
            retryResponse.statusText ||
            "Server returned an invalid response.",
          request_id:
            retryResponse.headers.get("x-request-id") ??
            responseRequestId,
        });
      }

      let retryJson: unknown;

      try {
        retryJson = await retryResponse.json();
      } catch {
        throw new APIClientError({
          code: `HTTP_${retryResponse.status}`,
          message: "Malformed server response",
          request_id:
            retryResponse.headers.get("x-request-id") ??
            responseRequestId,
        });
      }

      const retryPayload = retryJson as any;

      if (
        retryPayload &&
        typeof retryPayload === "object" &&
        "data" in retryPayload &&
        retryPayload.data !== undefined
      ) {
        return retryPayload as APIResponse<T>;
      }

      return {
        success: true,
        data: retryPayload as T,
        request_id:
          retryResponse.headers.get("x-request-id") ??
          responseRequestId,
      };
    }

    let jsonPayload: unknown;

    try {
      jsonPayload = await response.json();
    } catch {
      throw new APIClientError({
        code: `HTTP_${response.status}`,
        message:
          response.statusText || "Malformed server response",
        request_id: responseRequestId,
      });
    }

    /**
     * Handle non-2xx responses.
     */
    if (!response.ok) {
      /**
       * Automatically refresh the token on 401.
       */
      if (
        response.status === 401 &&
        !endpoint.includes("/api/v1/auth/")
      ) {
        const refreshedToken = await attemptTokenRefresh();

        if (refreshedToken) {
          const retryHeaders: Record<string, string> = {
            ...headers,
            ...NO_CACHE_HEADERS,
            Authorization: `Bearer ${refreshedToken}`,
          };

          const retryTarget =
            method === "GET" || method === "HEAD"
              ? addCacheBuster(originalTarget)
              : originalTarget;

          const retryResponse = await fetch(retryTarget, {
            ...options,
            method,
            credentials: options.credentials ?? "include",
            headers: retryHeaders,
            signal: controller.signal,
            cache: "no-store",
          });

          if (retryResponse.ok) {
            let retryJson: unknown;

            try {
              retryJson = await retryResponse.json();
            } catch {
              throw new APIClientError({
                code: `HTTP_${retryResponse.status}`,
                message: "Malformed server response",
                request_id:
                  retryResponse.headers.get("x-request-id") ??
                  responseRequestId,
              });
            }

            const retryPayload = retryJson as any;

            if (
              retryPayload &&
              typeof retryPayload === "object" &&
              "data" in retryPayload &&
              retryPayload.data !== undefined
            ) {
              return retryPayload as APIResponse<T>;
            }

            return {
              success: true,
              data: retryPayload as T,
              request_id:
                retryResponse.headers.get("x-request-id") ??
                responseRequestId,
            };
          }
        }
      }

      const err = jsonPayload as {
        error?: APIErrorDetail;
      };

      throw new APIClientError({
        code:
          err?.error?.code ??
          `HTTP_${response.status}`,

        message:
          err?.error?.message ??
          "An error occurred while communicating with the server.",

        request_id:
          err?.error?.request_id ??
          responseRequestId,

        details: err?.error?.details,
      });
    }

    /**
     * Successful JSON response.
     */
    const payload = jsonPayload as any;

    if (
      payload &&
      typeof payload === "object" &&
      "data" in payload &&
      payload.data !== undefined
    ) {
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

    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw new APIClientError({
        code: "TIMEOUT",
        message:
          "The server took too long to respond. Please check your connection and retry.",
      });
    }

    throw new APIClientError({
      code: "NETWORK_ERROR",
      message:
        "Unable to reach server. Please ensure the backend is running.",
    });
  } finally {
    clearTimeout(timeoutId);
  }
}