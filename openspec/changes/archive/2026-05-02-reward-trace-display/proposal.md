## Why

When reviewing agent traces, the reward number alone (e.g. `+0.11`) gives no insight into why the environment awarded it. Developers and researchers need to understand the reward signal at each step — whether a tool call was classified as relevant, repeated, or invalid, and which components contributed — to evaluate agent behaviour, debug reward shaping, and improve scenarios.

## What Changes

- `grading/rewards.py`: extend `compute_step_reward` to return a structured `RewardBreakdown` object alongside the scalar, capturing components and a human-readable reason string.
- `server/sentinel_environment.py`: attach the reward breakdown to the observation / step result so it is propagated to callers.
- `inference.py`: write `reward_breakdown` into the `env_response` block of each trace step.
- `ui/frontend/src/types.ts`: add `reward_breakdown` to `EnvResponse` type.
- `ui/frontend/src/views/TraceViewer.tsx`: display the breakdown inline in `StepDetail`, showing each component and the reason string (collapsed by default, expandable).

## Capabilities

### New Capabilities

- `reward-breakdown`: Structured per-step reward breakdown capturing individual reward components (step cost, relevance/repeated/invalid bonus) and a human-readable reason string; emitted by the grading layer, stored in traces, and displayed in the UI trace viewer.

### Modified Capabilities

<!-- No existing spec-level requirements change -->

## Impact

- `grading/rewards.py` — return type changes from `float` to a dataclass/typed dict; callers must be updated.
- `server/sentinel_environment.py` — env_response construction updated to include breakdown field.
- `inference.py` — trace serialisation includes `reward_breakdown` in each step's `env_response`.
- `ui/frontend/src/types.ts` — `EnvResponse` gains optional `reward_breakdown` field.
- `ui/frontend/src/views/TraceViewer.tsx` — new UI section per step.
- No breaking changes to the WebSocket/OpenEnv protocol; `reward` at the envelope level is unchanged.
- Existing trace files without `reward_breakdown` remain readable (field is optional).
