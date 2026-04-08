---
title: OpenEnv-Sentinel
emoji: 🚨
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
app_port: 8000
tags:
  - openenv
---

# OpenEnv-Sentinel: SRE Incident Triage Environment

An OpenEnv environment that simulates SRE incident triage. An AI agent receives a degraded system state and must use diagnostic tools to identify the root cause and recommend a fix.

## Quick Start

```bash
pip install -e .
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Or with Docker:

```bash
docker build -t sentinel-env -f server/Dockerfile .
docker run -p 8000:8000 sentinel-env
```

## Action Space

```python
class SentinelAction(Action):
    tool_name: str    # Tool to invoke
    parameters: dict  # Tool-specific parameters
```

### Available Tools

| Tool | Parameters | Description |
|---|---|---|
| `query_logs` | `service`, `query`, `severity` | Search service logs |
| `query_metrics` | `service`, `metric` | Get time-series metrics (cpu/memory/error_rate/latency/connections) |
| `get_service_status` | `service` | Service health, uptime, errors |
| `get_dependency_map` | `service` (optional) | Service dependency graph |
| `consult_runbook` | `topic` | SOP/runbook lookup |
| `check_recent_changes` | `service` (optional) | Recent deployments/config changes |
| `submit_resolution` | `root_cause`, `affected_service`, `recommendation` | Submit final answer (ends episode) |

## Observation Space

```python
class SentinelObservation(Observation):
    incident_summary: str       # Alert description
    tool_output: str            # Result from last tool call
    available_tools: list[str]  # Available tool names
    step_number: int            # Current step (0-indexed)
    max_steps: int              # Episode limit (20)
    cumulative_reward: float    # Running reward total
    last_action_error: str      # Error message if action was invalid
    done: bool                  # Episode finished?
    reward: float | None        # Per-step reward
```

## Tasks

### Task 1 — The Smoking Gun (Easy)
**Alert:** payment-api returning HTTP 500 errors. Straightforward single-service crash with a clear root cause in logs and deploy history. Optimal: 2–3 tool calls.

### Task 2 — The Upstream Culprit (Medium)
**Alert:** checkout-service p99 latency > 5 seconds. Requires tracing a dependency chain to find the real culprit (inventory-service OOM). Optimal: 4–6 tool calls.

### Task 3 — The Cascading Failure (Hard)
**Alert:** Multiple services degraded simultaneously. A long-running analytics query exhausts the PostgreSQL connection pool, cascading through auth, user-profile, and notification services. Includes red herrings. Optimal: 6–10 tool calls.

## Scoring

Each task is scored 0.0–1.0 using deterministic keyword-based grading:
- **Root cause identification** (weighted by task)
- **Correct affected service** identification
- **Actionable recommendation**
- **Efficiency bonus** (fewer steps = higher score)
- **Destructive penalty** (recommending harmful actions = score deduction)

Per-step rewards provide partial credit signal:
- Relevant tool call: +0.12
- Irrelevant tool call: −0.02
- Repeated call: −0.05
- Invalid action: −0.03
- Step cost: −0.01

## Running Inference

Uses `OpenAI(base_url=...)` — compatible with HF Inference, OpenAI, and any
OpenAI-compatible API.

```bash
# Environment server URL
export ENV_URL=http://localhost:8000

# LLM config (defaults to HF router)
export API_BASE_URL=https://router.huggingface.co/v1  # default, can omit
export MODEL_NAME=openai/gpt-oss-120b:novita           # default, can omit
export API_KEY=your-key      # or HF_TOKEN or OPENAI_API_KEY

pip install openai websockets
python inference.py
```

Output:
```
Task 1: 0.85
Task 2: 0.65
Task 3: 0.40
Average: 0.63
```

## Baseline Scores

| Task | GPT-4o (expected) | Open LLM (expected) |
|---|---|---|
| Task 1 (Easy) | 0.80–0.95 | 0.60–0.80 |
| Task 2 (Medium) | 0.60–0.80 | 0.40–0.60 |
| Task 3 (Hard) | 0.30–0.60 | 0.15–0.35 |

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/reset` | POST | Reset environment (`{"task_id": 1\|2\|3}`) |
| `/step` | POST | Execute action (`{"action": {...}}`) |
| `/state` | GET | Get current state |
| `/schema` | GET | JSON schemas for action/observation/state |
| `/ws` | WebSocket | Persistent session |
