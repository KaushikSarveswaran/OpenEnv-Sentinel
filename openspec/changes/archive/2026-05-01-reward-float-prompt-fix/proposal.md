## Why

Three distinct issues reduce evaluation fidelity: `reward` being `Optional[float]` introduces null-handling complexity and is semantically wrong (every step produces a reward); the `SYSTEM_PROMPT` in `inference.py` leaks the investigation strategy with a prescriptive step-by-step plan and upstream-bias hints, inflating scores artificially; and the `get_relevant_tools()` lists in Task 2 and Task 3 have key mismatches that cause valid relevant calls to be scored as irrelevant.

## What Changes

- **`models.py`**: Change `SentinelObservation.reward` from `Optional[float] = None` to `float = 0.0` — every step always has a reward value.
- **`inference.py` SYSTEM_PROMPT**: Remove the hardcoded step-by-step investigation plan and explicit upstream-root-cause hints. Build tool call format from the observation's `tool_descriptions` dynamically in `build_initial_prompt`. Keep JSON-only format constraint.
- **`scenarios/task3_cascading_failure.py`**: Replace `"query_metrics:analytics-worker"` (no metric suffix — never matches a real call) with `"query_metrics:analytics-worker:cpu"` and `"query_metrics:analytics-worker:memory"`.
- **`scenarios/task2_upstream_culprit.py`**: Add `"get_dependency_map"` (full map, no service param) to the relevance list since identifying the upstream relationship requires it.

## Capabilities

### New Capabilities
- `reward-non-optional`: `SentinelObservation.reward` is always a `float`; consumers no longer need null guards.

### Modified Capabilities
- `step-env-output-display`: Reward field type change may affect how the UI/trace consumers render or check the reward value (was Optional, now always present).

## Impact

- `models.py` — type change on `SentinelObservation.reward`
- `inference.py` — SYSTEM_PROMPT and `build_initial_prompt` rewritten
- `scenarios/task2_upstream_culprit.py` — `get_relevant_tools()` list updated
- `scenarios/task3_cascading_failure.py` — `get_relevant_tools()` list updated
- Tests in `tests/test_grading.py` and `tests/test_models.py` may need updating for the type change and new relevance keys
