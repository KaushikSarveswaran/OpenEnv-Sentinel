import { useState, useCallback, useEffect, useRef } from "react";
import ModelSelection from "../components/ModelSelection";
import ConsoleOutput from "../components/ConsoleOutput";
import type { Defaults, ModelQueueItem, RunStatus } from "../types";
import { startRun, cancelRun, streamRunOutput, fetchRunStatus } from "../api";

interface Props {
  defaults: Defaults | null;
}

export default function RunView({ defaults }: Props) {
  const [queue, setQueue] = useState<ModelQueueItem[]>([]);
  const [envUrl, setEnvUrl] = useState(defaults?.env_url ?? "http://localhost:8000");
  const [lines, setLines] = useState<string[]>([]);
  const [status, setStatus] = useState<RunStatus["status"]>("idle");
  const [progress, setProgress] = useState({ index: 0, total: 0 });
  const [error, setError] = useState("");
  const closeStreamRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    fetchRunStatus().then((s: RunStatus) => {
      if (s.status === "running") {
        setStatus("running");
        setProgress({ index: s.model_index, total: s.total_models });
        subscribeToStream();
      }
    });
    return () => {
      closeStreamRef.current?.();
    };
  }, []);

  const subscribeToStream = () => {
    closeStreamRef.current?.();
    const close = streamRunOutput(
      (msg: unknown) => {
        const m = msg as { type: string; data: unknown };
        if (m.type === "output") {
          setLines((prev) => [...prev, m.data as string]);
        } else if (m.type === "status") {
          const s = m.data as RunStatus;
          setStatus(s.status);
          setProgress({ index: s.model_index, total: s.total_models });
        }
      },
      () => {
        closeStreamRef.current = null;
      },
    );
    closeStreamRef.current = close;
  };

  const handleAdd = useCallback((item: ModelQueueItem) => {
    setQueue((q) => [...q, item]);
  }, []);

  const handleRemove = useCallback((index: number) => {
    setQueue((q) => q.filter((_, i) => i !== index));
  }, []);

  const handleRun = async () => {
    if (queue.length === 0) {
      setError("Add at least one model to the queue before running.");
      return;
    }
    setError("");
    setLines([]);
    setStatus("running");

    try {
      await startRun({ models: queue, env_url: envUrl });
      subscribeToStream();
    } catch (e) {
      setError((e as Error).message);
      setStatus("idle");
    }
  };

  const handleCancel = async () => {
    try {
      await cancelRun();
      closeStreamRef.current?.();
      setStatus("cancelled");
    } catch {
      /* ignore */
    }
  };

  if (!defaults) return <div className="loading">Loading defaults...</div>;

  return (
    <div className="run-view">
      <h2>Run Inference</h2>

      <div className="form-group">
        <label>Environment URL</label>
        <input value={envUrl} onChange={(e) => setEnvUrl(e.target.value)} />
      </div>

      <ModelSelection
        azure={defaults.azure}
        openrouter={defaults.openrouter}
        queue={queue}
        onAdd={handleAdd}
        onRemove={handleRemove}
      />

      <div className="run-controls">
        {status === "running" ? (
          <>
            <button className="btn btn-cancel" onClick={handleCancel}>Cancel</button>
            <span className="run-progress">
              Running {progress.index + 1}/{progress.total}
            </span>
          </>
        ) : (
          <button className="btn btn-run" onClick={handleRun} disabled={queue.length === 0}>
            Run ({queue.length} model{queue.length !== 1 ? "s" : ""})
          </button>
        )}
        {status === "completed" && <span className="status-badge completed">Completed</span>}
        {status === "failed" && <span className="status-badge failed">Failed</span>}
        {status === "cancelled" && <span className="status-badge cancelled">Cancelled</span>}
      </div>

      {error && <div className="error-msg">{error}</div>}

      {queue.length === 0 && status === "idle" && (
        <div className="empty-state">
          Select a provider above and add models to the queue to get started.
        </div>
      )}

      {lines.length > 0 && <ConsoleOutput lines={lines} />}
    </div>
  );
}
