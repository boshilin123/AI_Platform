import type { ApiError, ApiSuccess } from "../types/api";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const adminTokenKey = "bluedot-admin-session";

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly requestId: string,
    public readonly retryable: boolean,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

function headers(hasBody: boolean): HeadersInit {
  const result: Record<string, string> = {
    "X-Caller-System": "bluedot-ai-platform-web",
  };
  if (hasBody) result["Content-Type"] = "application/json";
  return result;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<ApiSuccess<T>> {
  const hasJsonBody = Boolean(init.body) && !(init.body instanceof FormData);
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      ...headers(hasJsonBody),
      ...(init.headers ?? {}),
    },
  });

  const payload = (await response.json()) as ApiSuccess<T> | ApiError;
  if (!response.ok || !payload.success) {
    const error = payload as ApiError;
    throw new ApiClientError(
      error.error?.message ?? "服务请求失败",
      error.error?.code ?? "AI_INTERNAL_ERROR",
      error.requestId ?? response.headers.get("X-Request-ID") ?? "",
      error.error?.retryable ?? false,
    );
  }
  return payload;
}

export function readAdminToken(): string {
  return sessionStorage.getItem(adminTokenKey) ?? "";
}

export function saveAdminToken(token: string): void {
  sessionStorage.setItem(adminTokenKey, token);
}

export function clearAdminToken(): void {
  sessionStorage.removeItem(adminTokenKey);
}

export async function adminApiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<ApiSuccess<T>> {
  const token = readAdminToken();
  return apiRequest<T>(path, {
    ...init,
    headers: {
      ...(init.headers ?? {}),
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function downloadAuditCsv(query: string): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/v1/audits/export${query}`, {
    headers: headers(false),
  });
  if (!response.ok) throw new Error("导出调用记录失败");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `ai-audits-${new Date().toISOString().slice(0, 10)}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}
