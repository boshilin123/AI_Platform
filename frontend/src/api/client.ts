import type { ApiError, ApiSuccess } from "../types/api";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const internalToken = import.meta.env.VITE_INTERNAL_API_TOKEN ?? "";

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
  if (internalToken) result["X-Internal-Token"] = internalToken;
  return result;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<ApiSuccess<T>> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      ...headers(Boolean(init.body)),
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
