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

export interface SpeechAudioResult {
  blob: Blob;
  requestId: string;
  model: string;
  voice: string;
  format: string;
  speed: number;
}

export interface SpeechSynthesisPayload {
  text: string;
  voice: string;
  responseFormat: "mp3" | "wav";
  speed: number;
}

export interface SpeechStreamSession {
  audioUrl: string;
  requestId: string;
  model: string;
  voice: string;
  format: string;
  speed: number;
  segmentCount: number;
  progressive: boolean;
  completion: Promise<Blob>;
  cancel: () => void;
}

async function speechApiError(response: Response): Promise<ApiClientError> {
  let error: ApiError | null = null;
  try {
    error = (await response.json()) as ApiError;
  } catch {
    // Binary streaming errors that happen after headers cannot carry the JSON envelope.
  }
  return new ApiClientError(
    error?.error?.message ?? "语音生成失败",
    error?.error?.code ?? "AI_INTERNAL_ERROR",
    error?.requestId ?? response.headers.get("X-Request-ID") ?? "",
    error?.error?.retryable ?? false,
  );
}

export async function synthesizeSpeech(
  payload: SpeechSynthesisPayload,
): Promise<SpeechAudioResult> {
  const response = await fetch(`${apiBaseUrl}/api/v1/tts/synthesize`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw await speechApiError(response);
  }
  return {
    blob: await response.blob(),
    requestId: response.headers.get("X-Request-ID") ?? "",
    model: response.headers.get("X-Audio-Model") ?? "",
    voice: response.headers.get("X-Audio-Voice") ?? payload.voice,
    format: response.headers.get("X-Audio-Format") ?? payload.responseFormat,
    speed: Number(response.headers.get("X-Audio-Speed") ?? payload.speed),
  };
}

export function supportsProgressiveMp3(): boolean {
  return (
    typeof MediaSource !== "undefined" &&
    typeof MediaSource.isTypeSupported === "function" &&
    MediaSource.isTypeSupported("audio/mpeg")
  );
}

function waitForSourceOpen(mediaSource: MediaSource): Promise<void> {
  if (mediaSource.readyState === "open") return Promise.resolve();
  return new Promise((resolve, reject) => {
    const opened = (): void => {
      cleanup();
      resolve();
    };
    const failed = (): void => {
      cleanup();
      reject(new Error("浏览器无法初始化流式音频播放器"));
    };
    const cleanup = (): void => {
      mediaSource.removeEventListener("sourceopen", opened);
      mediaSource.removeEventListener("sourceclose", failed);
    };
    mediaSource.addEventListener("sourceopen", opened, { once: true });
    mediaSource.addEventListener("sourceclose", failed, { once: true });
  });
}

function appendAudioChunk(sourceBuffer: SourceBuffer, chunk: Uint8Array): Promise<void> {
  return new Promise((resolve, reject) => {
    const completed = (): void => {
      cleanup();
      resolve();
    };
    const failed = (): void => {
      cleanup();
      reject(new Error("浏览器追加流式音频失败"));
    };
    const cleanup = (): void => {
      sourceBuffer.removeEventListener("updateend", completed);
      sourceBuffer.removeEventListener("error", failed);
    };
    sourceBuffer.addEventListener("updateend", completed, { once: true });
    sourceBuffer.addEventListener("error", failed, { once: true });
    const copy = chunk.slice();
    sourceBuffer.appendBuffer(copy.buffer as ArrayBuffer);
  });
}

export async function startSpeechStream(
  payload: SpeechSynthesisPayload,
  controller: AbortController = new AbortController(),
): Promise<SpeechStreamSession> {
  const response = await fetch(`${apiBaseUrl}/api/v1/tts/synthesize-stream`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify({ ...payload, responseFormat: "mp3" }),
    signal: controller.signal,
  });
  if (!response.ok) {
    throw await speechApiError(response);
  }

  const requestId = response.headers.get("X-Request-ID") ?? "";
  const model = response.headers.get("X-Audio-Model") ?? "";
  const voice = response.headers.get("X-Audio-Voice") ?? payload.voice;
  const contentType = response.headers.get("Content-Type")?.split(";")[0] ?? "";
  const format = contentType.includes("wav")
    ? "wav"
    : response.headers.get("X-Audio-Format") ?? "mp3";
  const speed = Number(response.headers.get("X-Audio-Speed") ?? payload.speed);
  const segmentCount = Number(response.headers.get("X-Audio-Segments") ?? "1");
  const progressive =
    Boolean(response.body) &&
    ["audio/mpeg", "audio/mp3", "application/octet-stream"].includes(contentType) &&
    supportsProgressiveMp3();

  if (!progressive || !response.body) {
    const blob = await response.blob();
    return {
      audioUrl: URL.createObjectURL(blob),
      requestId,
      model,
      voice,
      format,
      speed: Number.isFinite(speed) ? speed : payload.speed,
      segmentCount,
      progressive: false,
      completion: Promise.resolve(blob),
      cancel: () => controller.abort(),
    };
  }

  const mediaSource = new MediaSource();
  const audioUrl = URL.createObjectURL(mediaSource);
  const completion = (async (): Promise<Blob> => {
    const parts: ArrayBuffer[] = [];
    try {
      await waitForSourceOpen(mediaSource);
      const sourceBuffer = mediaSource.addSourceBuffer("audio/mpeg");
      try {
        sourceBuffer.mode = "sequence";
      } catch {
        // Some browsers expose a read-only mode for raw MPEG audio.
      }
      const reader = response.body!.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (!value?.byteLength) continue;
        const copy = value.slice();
        parts.push(copy.buffer as ArrayBuffer);
        await appendAudioChunk(sourceBuffer, copy);
      }
      if (mediaSource.readyState === "open") mediaSource.endOfStream();
      return new Blob(parts, { type: "audio/mpeg" });
    } catch (reason) {
      if (mediaSource.readyState === "open") {
        try {
          mediaSource.endOfStream("network");
        } catch {
          // The source may already have been closed by the browser.
        }
      }
      if (reason instanceof DOMException && reason.name === "AbortError") throw reason;
      throw new ApiClientError(
        "流式音频传输中断，请重新生成",
        "AI_STREAM_INTERRUPTED",
        requestId,
        false,
      );
    }
  })();

  return {
    audioUrl,
    requestId,
    model,
    voice,
    format,
    speed: Number.isFinite(speed) ? speed : payload.speed,
    segmentCount: Number.isFinite(segmentCount) ? segmentCount : 1,
    progressive: true,
    completion,
    cancel: () => controller.abort(),
  };
}
