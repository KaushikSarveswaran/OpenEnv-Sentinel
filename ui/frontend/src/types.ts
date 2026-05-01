export interface FreeModel {
  id: string;
  name: string;
  context: string;
}

export interface AzureDefaults {
  endpoint: string;
  deployment: string;
  api_key: string;
  api_version: string;
}

export interface OpenRouterDefaults {
  api_key: string;
  model_id: string;
  site_url: string;
  site_name: string;
  free_models: FreeModel[];
}

export interface Defaults {
  azure: AzureDefaults;
  openrouter: OpenRouterDefaults;
  env_url: string;
}

export interface ModelQueueItem {
  provider: "azure" | "openrouter";
  model_name: string;
  config: Record<string, string>;
}

export interface RunStatus {
  status: "idle" | "running" | "completed" | "failed" | "cancelled";
  model_index: number;
  total_models: number;
  output_lines: number;
}

export interface TraceSummary {
  filename: string;
  model_name: string;
  average_score: number;
  timestamp: string;
  total_tasks: number;
}

export interface TraceStep {
  step_number: number;
  llm_call: {
    messages_sent: { role: string; content: string }[];
    raw_output: string;
    parse_attempts: number;
    forced_resolution: boolean;
    latency_seconds: number;
    token_usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number } | null;
  };
  parsed_action: {
    tool_name: string;
    parameters: Record<string, unknown>;
  };
  env_response: {
    tool_output: string;
    reward: number;
    cumulative_reward: number;
    done: boolean;
    error: string;
  };
}

export interface TraceTask {
  task_id: number;
  incident_summary: string;
  final_score: number;
  total_steps: number;
  total_llm_calls: number;
  steps: TraceStep[];
  error?: string;
}

export interface TraceData {
  metadata: {
    model_name: string;
    api_base_url: string;
    env_url: string;
    timestamp: string;
    total_tasks: number;
    average_score: number;
  };
  tasks: TraceTask[];
}
