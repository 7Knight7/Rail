export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const API_BASE = "/api/v1";
export const API_TIMEOUT_MS = 15_000;
export const AUTOMATION_START_TIMEOUT_MS = 180_000;

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init?: RequestInit,
  timeoutMs = API_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal,
    });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

let csrfToken: string | null = null;
let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

export function getCsrfToken(): string | null {
  return csrfToken;
}

async function tryRefreshToken(): Promise<boolean> {
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.csrf_token) {
          setCsrfToken(data.csrf_token);
        }
        return true;
      }
      return false;
    } catch {
      return false;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
  skipAuthRetry = false,
  timeoutMs = API_TIMEOUT_MS,
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (init?.headers) {
    const initHeaders = init.headers as Record<string, string>;
    Object.assign(headers, initHeaders);
  }

  if (init?.body && typeof init.body === "string") {
    headers["Content-Type"] = "application/json";
  }

  if (csrfToken && init?.method && ["POST", "PUT", "DELETE", "PATCH"].includes(init.method)) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  const response = await fetchWithTimeout(`${API_BASE}${path}`, {
    credentials: "include",
    ...init,
    headers,
  }, timeoutMs);

  if (response.status === 401 && !skipAuthRetry && !path.includes("/auth/login") && !path.includes("/auth/refresh")) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return apiRequest(path, init, true, timeoutMs);
    }
    
    window.dispatchEvent(new window.CustomEvent("auth:session-expired"));
    throw new ApiError("Session expired", 401);
  }

  if (!response.ok) {
    let message: string;
    try {
      const errorData = await response.json();
      message = errorData.detail || errorData.message || JSON.stringify(errorData);
    } catch {
      message = await response.text() || `Request failed with status ${response.status}`;
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export { buildQueryString } from "./query";
