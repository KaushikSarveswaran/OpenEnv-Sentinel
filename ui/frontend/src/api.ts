const API = "/api";
const RUN_API = "http://localhost:8502";

export async function fetchDefaults() {
  const res = await fetch(`${API}/defaults`);
  return res.json();
}

export async function startRun(body: { models: unknown[]; env_url: string }) {
  const res = await fetch(`${RUN_API}/api/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to start run");
  }
  return res.json();
}

export async function cancelRun() {
  const res = await fetch(`${RUN_API}/api/run/cancel`, { method: "POST" });
  return res.json();
}

export async function fetchRunStatus() {
  const res = await fetch(`${RUN_API}/api/run/status`);
  return res.json();
}

export async function fetchTraces() {
  const res = await fetch(`${API}/traces`);
  return res.json();
}

export async function fetchTrace(filename: string) {
  const res = await fetch(`${API}/traces/${encodeURIComponent(filename)}`);
  if (!res.ok) throw new Error("Trace not found");
  return res.json();
}

export function streamRunOutput(onMessage: (data: unknown) => void, onDone: () => void) {
  const es = new EventSource(`${RUN_API}/api/run/stream`);
  es.onmessage = (e) => {
    const parsed = JSON.parse(e.data);
    onMessage(parsed);
  };
  es.onerror = () => {
    es.close();
    onDone();
  };
  return () => es.close();
}
