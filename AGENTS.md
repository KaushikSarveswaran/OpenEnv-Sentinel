# OpenEnv-Sentinel — Agent Guidelines

An OpenEnv RL environment that simulates SRE incident triage. An AI agent interacts with a degraded system via diagnostic tools and must identify the root cause and recommend a fix.

## Build and Test

```bash
pip install -e ".[dev]"
uvicorn server.app:app --host 0.0.0.0 --port 8000
pytest
```

## RL Environment Overview

### Episode Lifecycle
1. `reset(task_id)` — loads the scenario, returns initial `SentinelObservation` with `incident_summary` and `tool_descriptions`.
2. Agent calls `step(action)` repeatedly — each action invokes one tool and returns an updated observation with `tool_output`, `reward`, and updated `cumulative_reward`.
3. Episode ends when the agent calls `submit_resolution` or `step_number` reaches `max_steps` (20). `done=True` is set in the observation.

### Action Space
Actions are typed discriminated unions keyed on `tool_name`. Each tool has a dedicated `*Action` + `*Params` class in `models.py`. Tool dispatch happens in `tools/registry.py`.

| Tool | Key Params | Purpose |
|------|-----------|---------|
| `query_logs` | `service`, `query`, `severity` | Search service logs |
| `query_metrics` | `service`, `metric` | Time-series metrics (cpu/memory/error_rate/latency/connections) |
| `get_service_status` | `service` | Health, uptime, error rate, recent restarts |
| `get_dependency_map` | `service` (optional) | Service dependency graph |
| `consult_runbook` | `topic` | SOP/runbook lookup |
| `check_recent_changes` | `service` (optional) | Recent deployments and config changes |
| `submit_resolution` | `root_cause`, `affected_service`, `recommendation` | Submit final answer — ends episode |

### Observation Space (`SentinelObservation`)
| Field | Type | Notes |
|-------|------|-------|
| `incident_summary` | `str` | Alert text — constant across steps |
| `tool_output` | `str` | Pre-scripted response from the scenario |
| `available_tools` | `list[str]` | Always the 7 tools above |
| `step_number` | `int` | 0-indexed |
| `max_steps` | `int` | 20 |
| `cumulative_reward` | `float` | Running total |
| `last_action_error` | `str` | Non-empty when action was invalid |
| `done` | `bool` | Episode finished |
| `reward` | `float` | Per-step reward (default `0.0` — never `None`) |
| `reasoning` | `str \| None` | LLM reasoning text (if enabled) |

### Reward Structure
Per-step rewards in `grading/rewards.py`:

| Event | Reward |
|-------|--------|
| Step cost (every step) | −0.01 |
| Relevant tool call | +0.12 |
| Irrelevant tool call | −0.02 |
| Repeated tool call | −0.05 |
| Invalid action | −0.03 |

Terminal score (0.0–1.0) from `grading/grader.py` delegates to `scenario.grade_resolution()` and weights root-cause identification, affected-service correctness, recommendation quality, and an efficiency bonus for fewer steps.

Relevance is determined per-scenario via `get_relevant_tools()`, which returns colon-joined keys like `"query_logs:auth-service"`. A call is relevant only if its computed key (`tool_name:service` or `tool_name:metric` etc.) appears in that list.

The environment also terminates early after 5 consecutive invalid actions (`MAX_CONSECUTIVE_INVALID = 5`).

### Reward Breakdown Convention

`compute_step_reward` returns `tuple[float, RewardBreakdown]`. **Always unpack both values** — do not call it expecting a plain float.

`RewardBreakdown` fields:
- `components: list[RewardComponent]` — ordered list of `(label, value)` pairs that sum to the total reward (e.g. `step_cost: -0.01`, `relevant: +0.12`).
- `classification: str` — one of `"relevant"`, `"irrelevant"`, `"repeated"`, `"invalid"`.
- `reason: str` — human-readable explanation (e.g. `"relevant tool call (query_logs:auth-service): +0.12, step cost: -0.01"`).

When writing tasks that touch `grading/rewards.py` or `server/sentinel_environment.py`:
- Unpack with `reward, breakdown = compute_step_reward(...)`.
- Attach `breakdown` to the step result so it reaches the trace writer.
- In `inference.py`, serialise with `dataclasses.asdict(breakdown)` into `env_response["reward_breakdown"]`.
- In TypeScript types, `reward_breakdown` is optional — guard before rendering (`step.env_response.reward_breakdown && ...`).

### WebSocket / OpenEnv Protocol
- `data["reward"]` is at the **top-level envelope**, not inside `data["observation"]`. Always read reward from `data["reward"]`.
- `data["observation"]` excludes `reward`, `done`, and `metadata` (serialized at the envelope level).

## Scenarios

Each scenario inherits `BaseScenario` (`scenarios/base.py`) and must implement:
- `get_incident_summary()` — alert text shown at episode start
- `get_services()` — service state data
- `get_tool_response(tool_name, params)` — pre-scripted tool outputs (all evidence is planted here)
- `get_relevant_tools()` — list of relevance keys for reward shaping
- `grade_resolution(resolution, step_count)` — terminal scoring logic
- `get_tool_descriptions()` — parameter metadata for LLM context

Do not embed scoring logic outside `grade_resolution`. Do not use randomness — tool outputs must be deterministic for reproducibility.

| Scenario | Class | Difficulty | Optimal Steps |
|----------|-------|-----------|--------------|
| Task 1 — The Smoking Gun | `SmokingGunScenario` | Easy | 2–3 |
| Task 2 — The Upstream Culprit | `UpstreamCulpritScenario` | Medium | 4–6 |
| Task 3 — The Cascading Failure | `CascadingFailureScenario` | Hard | 6–10 |

## Code Conventions

- Python 3.12. Pydantic v2 (`model_dump()`, not `.dict()`).
- New tools: add to `tools/registry.py` + matching `*Action`/`*Params` in `models.py`.
- New scenarios: add to `scenarios/`, register in `SCENARIOS` dict in `server/sentinel_environment.py`.
- Tests in `tests/`; use `httpx.AsyncClient` for FastAPI endpoint tests.
- Grading logic stays in `grading/` — never in scenario classes or the environment server.

## Traces and Inference

- `inference.py` runs the agent loop using any OpenAI-compatible API against the environment at `ENV_URL`.
- Traces written to `traces/explainability_trace_YYYYMMDD_HHMMSS.json`. Do not commit trace files.
- Reasoning and pass-through behaviour is configured via the `inference:` block in `openenv.yaml` (not env vars).

| Variable | Purpose |
|----------|---------|
| `ENV_URL` | Environment server URL (default: `http://localhost:8000`) |
| `HF_TOKEN` / `OPENAI_API_KEY` | LLM credentials |
| `API_BASE_URL` | OpenAI-compatible base URL |
| `MODEL_NAME` | Model name |

**Key inference constants** (`inference.py`):

| Constant | Default | Purpose |
|----------|---------|--------|
| `MAX_PARSE_RETRIES` | `3` | Retries when LLM output is not valid JSON |
| `MAX_RATELIMIT_RETRIES` | `8` | Extra retries on HTTP 429 rate-limit errors |
| `MAX_COMPLETION_TOKENS` | `16384` | Token budget per LLM call |
| `TASK_TIMEOUT` | `360` | Per-task timeout in seconds |

## OpenSpec Workflow

- Active changes: `openspec/changes/<name>/` — `proposal.md`, `design.md`, `tasks.md`, `specs/`
- Completed changes: `openspec/changes/archive/`
- Skills: `.github/skills/openspec-*/`
