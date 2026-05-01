## Context

The project has three interrelated correctness issues:

1. **`SentinelObservation.reward` is `Optional[float]`** — semantically incorrect since every step always produces a reward (even -0.01 step cost). Callers in inference.py and the UI trace reader must null-check a value that is never actually null after the first step fires.

2. **`SYSTEM_PROMPT` in `inference.py` hardcodes a prescriptive investigation plan** — "Step 1: get_dependency_map, Step 2: check_recent_changes…" and hints like "The ROOT CAUSE is often UPSTREAM." This inflates RL evaluation scores by coaching the agent on the exact sequence of relevant tool calls rather than letting it reason from evidence. The prompt also duplicates tool definitions that are already injected dynamically via `build_initial_prompt` from the observation's `tool_descriptions`.

3. **`get_relevant_tools()` key mismatches in Task 2 and Task 3** — `make_relevance_key` builds keys as `tool:service:metric` or `tool:topic`. Task 3 contains `"query_metrics:analytics-worker"` (no metric suffix) which only matches a call with no metric param, but agents always supply a metric. Task 2 is missing `"get_dependency_map"` (full map, no service) which is necessary to discover the upstream relationship.

## Goals / Non-Goals

**Goals:**
- Make `reward` a non-optional `float` with default `0.0` everywhere it appears
- Remove the investigation script and upstream hints from `SYSTEM_PROMPT`; replace with a minimal format-only prompt that uses dynamically generated tool format from the observation
- Correct `get_relevant_tools()` in Task 2 and Task 3 so that valid investigative tool calls receive the `REWARD_RELEVANT` bonus

**Non-Goals:**
- Changing the reward magnitude constants in `rewards.py`
- Redesigning how tool descriptions are stored or delivered by the server
- Adding new tools or scenarios

## Decisions

### Decision 1: `reward = 0.0` default (not `None`)

The environment always emits a reward via the WebSocket envelope. The observation's `reward` field is populated by `sentinel_environment.py` from `data["reward"]`. There is no legitimate case where reward is absent after a step. A `0.0` default is semantically correct (no penalty, no bonus at the initial reset frame).

**Alternative considered:** Keep `Optional[float]` and document it. Rejected because every consumer then needs a null guard and Pydantic serialization emits `null` rather than a number, which is unexpected for a numeric metric.

### Decision 2: Minimal non-prescriptive SYSTEM_PROMPT

Remove the numbered step plan and root-cause coaching. The system prompt should only describe the agent's role, the output format, and the constraint to use JSON. Tool call format examples are built at runtime from `tool_descriptions` in `build_initial_prompt`, so they remain accurate and scenario-specific.

**Alternative considered:** Keep the prescriptive plan but remove the upstream hint only. Rejected because the ordered step list (get_dependency_map first, check_recent_changes second, etc.) still coaches the agent on the exact relevant tool sequence, invalidating reward shaping.

### Decision 3: Fix relevant tool keys by expanding with specific metric suffixes

For Task 3, replace `"query_metrics:analytics-worker"` with `"query_metrics:analytics-worker:cpu"` and `"query_metrics:analytics-worker:memory"` — the two metrics actually present in the scenario. An agent checking either is doing valid relevant work.

For Task 2, add `"get_dependency_map"` (no service param) alongside the existing `"get_dependency_map:checkout-service"` since discovering the full topology is necessary to identify the upstream culprit.

**Alternative considered:** Change `make_relevance_key` to do prefix matching. Rejected as too broad — it would incorrectly reward unrelated metric queries against a service.

## Risks / Trade-offs

- **`reward` type change** → Any code that checks `if reward is not None` will still compile but the branch is now dead. Unit tests that assert `reward is None` on the reset observation will need updating. Low risk.
- **Prompt change** → Agent evaluation scores may decrease initially since the coaching is removed. This is the intended effect — scores become more meaningful, not inflated.
- **Relevance key additions** → Broadening Task 3's relevant tools increases the chance of a REWARD_RELEVANT hit per episode. This is correct: the prior keys were too narrow and were under-rewarding valid exploration.
