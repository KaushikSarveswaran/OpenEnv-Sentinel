import { useEffect, useState } from "react";
import type { TraceData, TraceTask, TraceStep } from "../types";
import { fetchTrace } from "../api";

interface Props {
  filename: string;
  onBack: () => void;
}

function LlmResponseBlock({ raw }: { raw: string }) {
  if (!raw) return <></>;

  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return <pre className="raw-output">{raw}</pre>;
  }

  const { reasoning, tool_name, parameters, ...rest } = parsed as {
    reasoning?: unknown;
    tool_name?: unknown;
    parameters?: Record<string, unknown>;
    [key: string]: unknown;
  };

  return (
    <div className="llm-resp-block">
      {reasoning != null && (
        <div className="llm-field" style={{ flexDirection: "column" }}>
          <span className="llm-label llm-label-reasoning">reasoning</span>
          <div className="llm-reasoning-text">{String(reasoning)}</div>
        </div>
      )}
      {tool_name != null && (
        <div className="llm-field">
          <span className="llm-label llm-label-tool">{String(tool_name)}</span>
        </div>
      )}
      {parameters != null && typeof parameters === "object" && (
        <div className="llm-field" style={{ flexDirection: "column" }}>
          <div className="llm-params">
            {Object.entries(parameters).map(([k, v]) => (
              <div key={k} className="llm-param-row">
                <span className="llm-param-key">{k}</span>
                <span className="llm-param-val">
                  {typeof v === "string" ? v : JSON.stringify(v)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      {Object.entries(rest).map(([k, v]) => (
        <div key={k} className="llm-field">
          <span className="llm-label llm-label-generic">{k}</span>
          <span className="llm-value">
            {typeof v === "string" ? v : JSON.stringify(v)}
          </span>
        </div>
      ))}
    </div>
  );
}

function StepDetail({ step }: { step: TraceStep }) {
  const [showMessages, setShowMessages] = useState(false);
  const [showFullOutput, setShowFullOutput] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);

  const toolOutput = step.env_response.tool_output;
  const outputTruncated = toolOutput && toolOutput.length > 500;
  const reasoning = step.llm_call.reasoning;
  const breakdown = step.env_response.reward_breakdown;

  return (
    <div className="step-detail">
      <div className="step-header">
        <span className="step-tool">{step.parsed_action.tool_name}</span>
        <span className="step-reward">reward: {step.env_response.reward.toFixed(2)}</span>
        {breakdown && (
          <button className="btn btn-xs btn-breakdown" onClick={() => setShowBreakdown(!showBreakdown)}>
            {showBreakdown ? "▾ why?" : "▸ why?"}
          </button>
        )}
        <span className="step-latency">{step.llm_call.latency_seconds}s</span>
        {step.llm_call.token_usage && (
          <span className="step-tokens">{step.llm_call.token_usage.total_tokens} tok</span>
        )}
        {step.llm_call.forced_resolution && <span className="badge forced">forced</span>}
        {step.env_response.error && <span className="badge error">error</span>}
      </div>
      <div className="step-params">
        <strong>Parameters:</strong> <code>{JSON.stringify(step.parsed_action.parameters)}</code>
      </div>
      {breakdown && showBreakdown && (
        <div className="step-breakdown">
          <div className="breakdown-reason">{breakdown.reason}</div>
          <table className="breakdown-table">
            <tbody>
              {breakdown.components.map((c, i) => (
                <tr key={i} className={`breakdown-row breakdown-${breakdown.classification}`}>
                  <td className="breakdown-label">{c.label}</td>
                  <td className={`breakdown-value ${c.value >= 0 ? "pos" : "neg"}`}>
                    {c.value >= 0 ? "+" : ""}{c.value.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {reasoning && (
        <div className="step-reasoning">
          <button className="btn btn-sm" onClick={() => setShowReasoning(!showReasoning)}>
            {showReasoning ? "Hide Reasoning" : "Show Reasoning"}
          </button>
          {showReasoning && (
            <>
              <strong>Reasoning:</strong>
              <pre className="reasoning-output">{reasoning}</pre>
            </>
          )}
        </div>
      )}
      {toolOutput && (
        <div className="step-tool-output">
          <strong>Tool Output:</strong>
          <pre className="tool-output">
            {showFullOutput || !outputTruncated
              ? toolOutput
              : toolOutput.substring(0, 500) + "..."}
          </pre>
          {outputTruncated && (
            <button className="btn btn-sm" onClick={() => setShowFullOutput(!showFullOutput)}>
              {showFullOutput ? "Hide" : "Show full output"}
            </button>
          )}
        </div>
      )}
      {step.env_response.error && (
        <div className="step-error">Error: {step.env_response.error}</div>
      )}
      <div className="step-meta">
        Cumulative reward: {step.env_response.cumulative_reward.toFixed(2)} |
        Parse attempts: {step.llm_call.parse_attempts}
      </div>
      <button className="btn btn-sm" onClick={() => setShowMessages(!showMessages)}>
        {showMessages ? "Hide Messages" : "Show Messages"}
      </button>
      {showMessages && (
        <div className="step-messages">
          <h5>Messages Sent ({step.llm_call.messages_sent.length})</h5>
          <pre className="messages-pre">
            {step.llm_call.messages_sent.map((m, i) => (
              <div key={i} className={`msg msg-${m.role}`}>
                <strong>[{m.role}]</strong> {m.content.substring(0, 500)}
                {m.content.length > 500 && "..."}
              </div>
            ))}
          </pre>
          <h5>Raw Output</h5>
          <LlmResponseBlock raw={step.llm_call.raw_output} />
        </div>
      )}
    </div>
  );
}

function TaskSection({ task }: { task: TraceTask }) {
  const [expanded, setExpanded] = useState(false);
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  return (
    <div className="task-section">
      <div className="task-header" onClick={() => setExpanded(!expanded)}>
        <span className="task-toggle">{expanded ? "▼" : "▶"}</span>
        <span className="task-id">Task {task.task_id}</span>
        <span className={`task-score ${task.final_score > 0.5 ? "good" : task.final_score > 0.1 ? "ok" : "low"}`}>
          {task.final_score.toFixed(4)}
        </span>
        <span className="task-meta">{task.total_steps} steps | {task.total_llm_calls} LLM calls</span>
      </div>
      {expanded && (
        <div className="task-body">
          <div className="task-summary">{task.incident_summary}</div>
          {task.error && <div className="task-error">Error: {task.error}</div>}
          <div className="steps-timeline">
            {task.steps.map((step, i) => (
              <div key={i} className={`step-row ${expandedStep === i ? "expanded" : ""}`}>
                <div className="step-brief" onClick={() => setExpandedStep(expandedStep === i ? null : i)}>
                  <span className="step-num">#{step.step_number}</span>
                  <span className="step-tool">{step.parsed_action.tool_name}</span>
                  <span className="step-reward-brief">{step.env_response.reward.toFixed(2)}</span>
                  {step.env_response.error && <span className="badge error">!</span>}
                </div>
                {expandedStep === i && <StepDetail step={step} />}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function TraceViewer({ filename, onBack }: Props) {
  const [trace, setTrace] = useState<TraceData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchTrace(filename)
      .then(setTrace)
      .finally(() => setLoading(false));
  }, [filename]);

  if (loading) return <div className="loading">Loading trace...</div>;
  if (!trace) return <div className="error-msg">Failed to load trace</div>;

  const m = trace.metadata;

  return (
    <div className="trace-viewer">
      <button className="btn btn-back" onClick={onBack}>← Back to History</button>

      <div className="trace-metadata">
        <h2>Trace: {m.model_name}</h2>
        <div className="metadata-grid">
          <div><strong>Model:</strong> {m.model_name}</div>
          <div><strong>API Base:</strong> {m.api_base_url}</div>
          <div><strong>Env URL:</strong> {m.env_url}</div>
          <div><strong>Timestamp:</strong> {new Date(m.timestamp).toLocaleString()}</div>
          <div><strong>Tasks:</strong> {m.total_tasks}</div>
          <div className={`avg-score ${m.average_score > 0.5 ? "good" : m.average_score > 0.1 ? "ok" : "low"}`}>
            <strong>Avg Score:</strong> {m.average_score.toFixed(4)}
          </div>
        </div>
      </div>

      <div className="tasks-list">
        {trace.tasks.map((task) => (
          <TaskSection key={task.task_id} task={task} />
        ))}
      </div>
    </div>
  );
}
