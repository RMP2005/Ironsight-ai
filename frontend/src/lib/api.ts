import type { ModelInfo, PredictionRequest, PredictionResponse } from "@/types/api";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

const GENERIC_API_ERROR = "Unable to complete the request. Please try again.";

const MAX_WAKE_WAIT_MS = 90_000;
const HEALTH_POLL_MS = 5_000;
const WAKE_STATUSES = new Set([408, 425, 429, 502, 503, 504]);

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getApiUrl(path: string): string {
  if (!apiBaseUrl) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }

  return `${apiBaseUrl.replace(/\/$/, "")}${path}`;
}

function looksUnsafe(text: string): boolean {
  const lower = text.toLowerCase();
  return (
    lower.includes("traceback") ||
    lower.includes("stack trace") ||
    lower.includes("file \"") ||
    lower.includes("file '") ||
    text.includes("\n  File ") ||
    text.length > 400
  );
}

function extractFastApiDetail(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const detail = (payload as { detail?: unknown }).detail;

  if (typeof detail === "string") {
    const trimmed = detail.trim();
    if (!trimmed || looksUnsafe(trimmed)) {
      return null;
    }
    return trimmed;
  }

  if (Array.isArray(detail)) {
    const messages: string[] = [];

    for (const item of detail) {
      if (typeof item === "string") {
        const trimmed = item.trim();
        if (trimmed && !looksUnsafe(trimmed)) {
          messages.push(trimmed);
        }
        continue;
      }

      if (item && typeof item === "object" && "msg" in item) {
        const msg = (item as { msg?: unknown }).msg;
        if (typeof msg === "string") {
          const trimmed = msg.trim();
          if (trimmed && !looksUnsafe(trimmed)) {
            messages.push(trimmed);
          }
        }
      }
    }

    if (messages.length === 0) {
      return null;
    }

    return messages.join(" ");
  }

  return null;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail: string | null = null;

    try {
      const payload: unknown = await response.json();
      detail = extractFastApiDetail(payload);
    } catch {
      detail = null;
    }

    throw new ApiError(detail ?? GENERIC_API_ERROR, response.status);
  }

  return response.json() as Promise<T>;
}

async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(getApiUrl("/health"), { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

// The Render free-tier backend sleeps after inactivity. On a network failure
// or gateway error, poll /health until the instance wakes, then retry once.
async function fetchWithWakeRetry(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const send = () => fetch(getApiUrl(path), init);

  let response: Response;
  try {
    response = await send();
  } catch (networkErr) {
    console.warn("[api] network failure, waiting for backend:", networkErr);
    response = await waitForBackend(send);
  }

  if (WAKE_STATUSES.has(response.status)) {
    console.warn("[api] gateway status", response.status, "— waiting for backend");
    response = await waitForBackend(send);
  }

  return response;
}

async function waitForBackend(send: () => Promise<Response>): Promise<Response> {
  const deadline = Date.now() + MAX_WAKE_WAIT_MS;
  while (Date.now() < deadline) {
    await sleep(HEALTH_POLL_MS);
    if (await checkHealth()) {
      console.log("[api] backend healthy, retrying request");
      return send();
    }
  }
  throw new ApiError(
    `Could not reach the backend after ${MAX_WAKE_WAIT_MS / 1000} seconds. ` +
      "The server may be asleep — please retry.",
    503,
  );
}

export async function getModelInfo(): Promise<ModelInfo> {
  const response = await fetchWithWakeRetry("/model-info");

  return parseResponse<ModelInfo>(response);
}

export async function predictMachine(
  request: PredictionRequest,
): Promise<PredictionResponse> {
  const response = await fetchWithWakeRetry("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  return parseResponse<PredictionResponse>(response);
}

export function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error && error.message === "NEXT_PUBLIC_API_BASE_URL is not configured.") {
    return "Analysis service URL is not configured.";
  }

  if (error instanceof TypeError) {
    return "Unable to reach the IronSight analysis service.";
  }

  return fallback;
}
