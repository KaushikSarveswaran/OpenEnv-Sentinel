import { useEffect, useState } from "react";
import type { TraceSummary } from "../types";
import { fetchTraces } from "../api";

interface Props {
  onSelect: (filename: string) => void;
  onCompare: (filenames: string[]) => void;
}

export default function HistoryView({ onSelect, onCompare }: Props) {
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchTraces()
      .then(setTraces)
      .finally(() => setLoading(false));
  }, []);

  const toggleSelect = (filename: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(filename)) next.delete(filename);
      else next.add(filename);
      return next;
    });
  };

  if (loading) return <div className="loading">Loading traces...</div>;

  if (traces.length === 0) {
    return (
      <div className="empty-state">
        <h2>History</h2>
        <p>No traces found in the <code>traces/</code> folder. Run an inference to generate traces.</p>
      </div>
    );
  }

  return (
    <div className="history-view">
      <div className="history-header">
        <h2>Run History</h2>
        {selected.size >= 2 && (
          <button className="btn btn-compare" onClick={() => onCompare(Array.from(selected))}>
            Compare ({selected.size})
          </button>
        )}
      </div>
      <table className="history-table">
        <thead>
          <tr>
            <th></th>
            <th>Model</th>
            <th>Score</th>
            <th>Tasks</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {traces.map((t) => (
            <tr key={t.filename} className="history-row" onClick={() => onSelect(t.filename)}>
              <td onClick={(e) => { e.stopPropagation(); toggleSelect(t.filename); }}>
                <input type="checkbox" checked={selected.has(t.filename)} readOnly />
              </td>
              <td className="model-col">{t.model_name}</td>
              <td className={`score-col ${t.average_score > 0.5 ? "good" : t.average_score > 0.1 ? "ok" : "low"}`}>
                {t.average_score.toFixed(4)}
              </td>
              <td>{t.total_tasks}</td>
              <td className="timestamp-col">{new Date(t.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
