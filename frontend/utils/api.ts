const base = () =>
  (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export type ChatPayload = {
  message: string;
  session_id?: string | null;
};

export type ChatResult = {
  answer: string;
  session_id: string;
  agent?: string | null;
  intent?: string | null;
  confidence?: number | null;
  escalated: boolean;
  sources: string[];
};

function formatFastApiDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: string }).msg);
        }
        return JSON.stringify(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return "Request failed";
}

export type ConfigStatus = {
  llm_configured: boolean;
  llm_provider?: string;
  openai_configured?: boolean;
  gemini_configured?: boolean;
};

export async function fetchConfigStatus(): Promise<ConfigStatus> {
  const res = await fetch(`${base()}/api/config`);
  if (!res.ok) return { llm_configured: false };
  const data = (await res.json()) as ConfigStatus;
  if (typeof data.llm_configured !== "boolean") {
    const legacy = data as { openai_configured?: boolean };
    return {
      ...data,
      llm_configured: Boolean(legacy.openai_configured),
    };
  }
  return data;
}

export async function sendChat(payload: ChatPayload): Promise<ChatResult> {
  const res = await fetch(`${base()}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: payload.message,
      session_id: payload.session_id || undefined,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = formatFastApiDetail((err as { detail?: unknown }).detail);
    throw new Error(detail || res.statusText);
  }
  return res.json();
}

export async function fetchSessions(): Promise<{session_id: string, title: string, ts: string}[]> {
  const res = await fetch(`${base()}/api/sessions`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.sessions || [];
}

export async function fetchSessionHistory(sessionId: string): Promise<{role: "user" | "assistant", text: string, meta?: any}[]> {
  const res = await fetch(`${base()}/api/session/${sessionId}`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.messages || [];
}
