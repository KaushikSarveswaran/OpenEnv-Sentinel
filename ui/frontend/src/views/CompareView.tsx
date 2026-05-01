import { useEffect, useState } from "react";
import type { TraceData } from "../types";
import { fetchTrace } from "../api";

interface Props {
  filenames: string[];
  onBack: () => void;
}

export default function CompareView({ filenames, onBack }: Props) {
  const [traces, setTraces] = useState<TraceData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all(filenames.map(fetchTrace))
      .then(setTraces)
      .finally(() => setLoading(false));
  }, [filenames]);

  if (loading) return <div className="loading">Loading traces for comparison...</div>;

  const taskIds = traces.length > 0
    ? traces[0].tasks.map((t) => t.task_id)
    : [];

  return (
    <div className="compare-view">
      <button className="btn btn-back" onClick={onBack}>← Back to History</button>
      <h2>Score Comparison</h2>
      <table className="compare-table">
        <thead>
          <tr>
            <th>Task</th>
            {traces.map((t, i) => (
              <th key={i}>{t.metadata.model_name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {taskIds.map((tid) => (
            <tr key={tid}>
              <td>Task {tid}</td>
              {traces.map((t, i) => {
                const task = t.tasks.find((tk) => tk.task_id === tid);
                const score = task?.final_score ?? 0;
                return (
                  <td key={i} className={score > 0.5 ? "good" : score > 0.1 ? "ok" : "low"}>
                    {score.toFixed(4)}
                  </td>
                );
              })}
            </tr>
          ))}
          <tr className="avg-row">
            <td><strong>Average</strong></td>
            {traces.map((t, i) => (
              <td key={i} className={t.metadata.average_score > 0.5 ? "good" : t.metadata.average_score > 0.1 ? "ok" : "low"}>
                <strong>{t.metadata.average_score.toFixed(4)}</strong>
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
