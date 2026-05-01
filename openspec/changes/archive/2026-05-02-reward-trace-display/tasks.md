## 1. Grading Layer — Reward Breakdown

- [x] 1.1 Add `RewardComponent` dataclass (`label: str`, `value: float`) to `grading/rewards.py`
- [x] 1.2 Add `RewardBreakdown` dataclass (`components: list[RewardComponent]`, `classification: str`, `reason: str`) to `grading/rewards.py`
- [x] 1.3 Change `compute_step_reward` return type to `tuple[float, RewardBreakdown]` and build the breakdown for each classification branch (invalid, repeated, relevant, irrelevant)
- [x] 1.4 Update all call sites in `server/sentinel_environment.py` to unpack the tuple — use `reward, breakdown = compute_step_reward(...)` and thread `breakdown` through to the step result

## 2. Trace Serialisation

- [x] 2.1 In `inference.py`, capture the `RewardBreakdown` returned from the env step response and include it as `reward_breakdown` in the `env_response` dict written per trace step (use `dataclasses.asdict` for serialisation)

## 3. TypeScript Types

- [x] 3.1 Add `RewardComponent` interface (`label: string; value: number`) to `ui/frontend/src/types.ts`
- [x] 3.2 Add `RewardBreakdown` interface (`components: RewardComponent[]; classification: string; reason: string`) to `ui/frontend/src/types.ts`
- [x] 3.3 Add optional `reward_breakdown?: RewardBreakdown` field to the `EnvResponse` interface in `ui/frontend/src/types.ts`

## 4. UI — Trace Viewer

- [x] 4.1 In `ui/frontend/src/views/TraceViewer.tsx`, add `showBreakdown` state to `StepDetail`
- [x] 4.2 Render a "why?" badge/button next to the reward value in the step header — only when `step.env_response.reward_breakdown` is present
- [x] 4.3 Render the collapsible breakdown panel inside `StepDetail`: show `reason` string and a list of each `component` with label and value when expanded

## 5. Tests

- [x] 5.1 Update `tests/test_grading.py` assertions for `compute_step_reward` to unpack the tuple and assert `breakdown.classification`, `breakdown.reason`, and `breakdown.components` for each reward path (invalid, repeated, relevant, irrelevant)
