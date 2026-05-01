## Context

Per-step rewards in `grading/rewards.py` are computed from several discrete components: a fixed step cost, plus one of four bonuses (relevant, irrelevant, repeated, invalid). Today `compute_step_reward` returns only a `float`. The reason behind the number is implicit in the code but invisible at runtime and not recorded in traces.

The UI trace viewer (`ui/frontend/src/views/TraceViewer.tsx`) shows the reward scalar next to each step but gives no insight into classification. Developers reviewing traces must mentally reconstruct why a step received a particular reward.

## Goals / Non-Goals

**Goals:**
- Expose a structured `RewardBreakdown` from `compute_step_reward` containing: individual components (label + value), classification label, and a human-readable reason string.
- Attach the breakdown to each step's env_response in `inference.py` trace output.
- Display the breakdown inline in the trace viewer UI, collapsed by default.

**Non-Goals:**
- Changing the scalar reward values or reward policy.
- Modifying the WebSocket/OpenEnv protocol envelope — `reward` at the envelope level is unchanged.
- Retroactively enriching old trace files (field is optional; old traces render without it).
- Exposing breakdown through the live WebSocket observation (only traces, not the RL env API).

## Decisions

### 1. Return a dataclass alongside the float, not a replacement

**Decision**: `compute_step_reward` returns `tuple[float, RewardBreakdown]` instead of changing the return type to `RewardBreakdown`.

**Rationale**: All existing callers expect a `float`. Returning a tuple is a minimal, explicit change — callers that only need the scalar ignore `[1]`. A `RewardBreakdown`-only return would require every caller to call `.total` or similar, increasing blast radius.

**Alternative considered**: `RewardBreakdown` with a `.reward` property — rejected because it requires changing call sites and creates an implicit convention.

### 2. `RewardBreakdown` as a `dataclass`, not a `TypedDict`

**Decision**: Use `@dataclass` with `components: list[RewardComponent]`, `classification: str`, `reason: str`.

**Rationale**: Dataclasses are idiomatic for structured value objects in this codebase (Pydantic models are used at API boundaries; dataclasses are fine for internal grading logic). `TypedDict` would work but gives weaker IDE support for the internal layer.

### 3. Breakdown stored in trace only, not in the live RL observation

**Decision**: `SentinelObservation` and the WebSocket envelope are not changed. `inference.py` extracts the breakdown from the env step response and embeds it in the trace JSON.

**Rationale**: The RL protocol is the stable public contract. Adding breakdown there would require env server changes and could affect external agents consuming the WebSocket. Traces are an internal artefact and can be extended freely.

### 4. UI display: collapsed pill with expand

**Decision**: Show a small badge (e.g. "▶ why?") next to the reward in the step header. Clicking expands a breakdown table showing each component row and the reason string.

**Rationale**: Consistent with how `Show Reasoning` and `Show Messages` already work in `StepDetail`. Collapsed-by-default keeps the timeline scannable.

## Risks / Trade-offs

- **Tuple return type is a minor breaking change inside the codebase** → All internal callers in `server/sentinel_environment.py` must be updated in the same PR. Unit tests for `compute_step_reward` will fail until updated. Mitigation: tasks include explicit test updates.
- **Trace files grow slightly** → Each step gains a small JSON object (~100 bytes). Not a meaningful concern.
- **Old traces lack `reward_breakdown`** → UI must handle the field being absent (`undefined`). Mitigation: field typed as optional in TypeScript; UI conditionally renders the badge.

## Migration Plan

1. Update `grading/rewards.py` — add `RewardComponent`, `RewardBreakdown`, change return to tuple.
2. Update `server/sentinel_environment.py` — unpack tuple, use scalar for reward, attach breakdown.
3. Update `inference.py` — include `reward_breakdown` in `env_response` dict written to trace.
4. Update `ui/frontend/src/types.ts` — add optional `reward_breakdown` to `EnvResponse`.
5. Update `ui/frontend/src/views/TraceViewer.tsx` — render breakdown badge + expand panel.
6. Update unit tests in `tests/test_grading.py` — assert tuple return and breakdown contents.

No rollback complexity — all changes are additive or backward-compatible.

## Open Questions

- None. Scope is clear and self-contained.
