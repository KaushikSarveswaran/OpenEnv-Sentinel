## 1. Fix `reward` Field Type in `SentinelObservation`

- [x] 1.1 In `models.py`, change `reward: Optional[float] = Field(default=None, ...)` to `reward: float = Field(default=0.0, ...)` and remove the `Optional` import if it becomes unused
- [x] 1.2 Search for any null-guard patterns on `reward` (e.g., `if reward is not None`, `reward or 0`) in `inference.py`, `server/sentinel_environment.py`, `ui/backend/`, and fix or remove them
- [x] 1.3 Update `tests/test_models.py` to assert `reward == 0.0` (float) on a fresh `SentinelObservation()` rather than `reward is None`
- [x] 1.4 Update `tests/test_grading.py` and `tests/test_environment.py` if any assertions check `reward is None`

## 2. Fix Relevant Tools Lists in Scenarios

- [x] 2.1 In `scenarios/task3_cascading_failure.py`, replace `"query_metrics:analytics-worker"` in `get_relevant_tools()` with `"query_metrics:analytics-worker:cpu"` and `"query_metrics:analytics-worker:memory"`
- [x] 2.2 In `scenarios/task2_upstream_culprit.py`, add `"get_dependency_map"` (no service suffix) to `get_relevant_tools()` so full-map queries are rewarded
- [x] 2.3 Run `pytest tests/test_grading.py tests/test_tools.py` and confirm all tests pass with the updated relevance lists

## 3. Rewrite `SYSTEM_PROMPT` in `inference.py`

- [x] 3.1 Remove the hardcoded "Available tools:" block and the numbered "INVESTIGATION PLAN" from `SYSTEM_PROMPT`
- [x] 3.2 Remove the coaching hints: "ROOT CAUSE is often UPSTREAM", "Look for: bad deployments…", the ordered step recommendations, and "You MUST call submit_resolution by step 10"
- [x] 3.3 Reduce `SYSTEM_PROMPT` to: role description, JSON-only format constraint, and a concise single-line format example for how to call a tool and for `submit_resolution`
- [x] 3.4 In `build_initial_prompt`, generate per-tool call format examples from `tool_descriptions` (the observation's available parameter metadata) rather than relying on the static system prompt list
- [x] 3.5 Keep the step-budget nudges in `build_tool_response_prompt` (they are format/pacing hints, not answer hints) — verify they still fire at the correct thresholds
- [x] 3.6 Run a quick smoke-test: start the environment server (`uvicorn server.app:app`) and run `inference.py` against task 1 to confirm the agent can complete an episode with the new prompt

## 4. Run Full Test Suite

- [x] 4.1 Run `pytest` from the project root and confirm all tests pass
- [x] 4.2 Verify no `Optional` import warnings or type errors via `python -m mypy models.py` (or equivalent)
