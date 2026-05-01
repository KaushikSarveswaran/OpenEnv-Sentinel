import { useEffect, useState } from "react";
import type { Defaults } from "./types";
import { fetchDefaults } from "./api";
import RunView from "./views/RunView";
import HistoryView from "./views/HistoryView";
import TraceViewer from "./views/TraceViewer";
import CompareView from "./views/CompareView";
import "./App.css";

type View = "run" | "history" | "trace" | "compare";

function getViewFromHash(): View {
  const hash = window.location.hash.slice(1);
  if (hash === "history" || hash === "trace" || hash === "compare") return hash as View;
  return "run";
}

export default function App() {
  const [view, setView] = useState<View>(getViewFromHash);
  const [defaults, setDefaults] = useState<Defaults | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<string>("");
  const [compareFiles, setCompareFiles] = useState<string[]>([]);

  useEffect(() => {
    fetchDefaults().then(setDefaults);
  }, []);

  useEffect(() => {
    const onHashChange = () => setView(getViewFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const navigate = (v: View) => {
    window.location.hash = v === "run" ? "" : v;
    setView(v);
  };

  const handleSelectTrace = (filename: string) => {
    setSelectedTrace(filename);
    navigate("trace");
  };

  const handleCompare = (filenames: string[]) => {
    setCompareFiles(filenames);
    navigate("compare");
  };

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="sidebar-title">Sentinel UI</div>
        <button className={view === "run" ? "active" : ""} onClick={() => navigate("run")}>
          Run
        </button>
        <button className={view === "history" ? "active" : ""} onClick={() => navigate("history")}>
          History
        </button>
      </nav>
      <main className="main-content">
        <div style={{ display: view === "run" ? "block" : "none" }}>
          <RunView defaults={defaults} />
        </div>
        {view === "history" && (
          <HistoryView onSelect={handleSelectTrace} onCompare={handleCompare} />
        )}
        {view === "trace" && selectedTrace && (
          <TraceViewer filename={selectedTrace} onBack={() => navigate("history")} />
        )}
        {view === "compare" && compareFiles.length >= 2 && (
          <CompareView filenames={compareFiles} onBack={() => navigate("history")} />
        )}
      </main>
    </div>
  );
}
