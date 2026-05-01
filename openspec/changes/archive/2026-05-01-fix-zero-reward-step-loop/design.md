## Context

Two defects affect inference runs launched via the UI:

1. **Zero rewards** — `inference.py` reads `reward` from the wrong level of the WebSocket response. OpenEnv's `serialize_observation` helper puts `reward` at the top-level `data` envelope and explicitly *excludes* it from the nested `observation` dict (via `model_dump(exclude={"reward", "done", "metadata"})`). The current code does `observation.get("reward", 0.0)`, which hits the inner dict and always falls back to `0.0`.

2. **Repeating terminal output** — The SSE stream endpoint in `run_service.py` calls `runner.get_output_since(0)` inside an infinite loop that runs every 0.3 s. Because `0` is hard-coded, every tick re-sends the entire accumulated output from the start. The frontend appends every received line, so the terminal grows as a repeated concatenation of the full run history after every polling cycle.

Both defects are isolated to a single line each in separate files.

## Goals / Non-Goals

**Goals:**
- Correct rewards are read from `data["reward"]` and logged in the `[STEP]` line and trace.
- SSE stream sends only new output lines to connected clients on each tick.
- No regressions to existing run, cancel, or history flows.

**Non-Goals:**
- Changing reward computation logic in `grading/rewards.py` or `server/sentinel_environment.py`.
- Altering the WebSocket protocol or the OpenEnv library.
- Frontend UI changes.

## Decisions

### D1 — Read reward from the `data` envelope, not `observation`

The WebSocket response format (from OpenEnv) is:
```
{ "data": { "observation": {...}, "reward": <float|null>, "done": <bool> } }
```
`inference.py` already unpacks `data = resp["data"]` and `observation = data.get("observation", data)`. The fix is to read `step_reward` from `data` rather than from `observation`:

```python
# Before
step_reward = observation.get("reward", 0.0)

# After
_raw_reward = data.get("reward")
step_reward = float(_raw_reward) if _raw_reward is not None else 0.0
```

`cumulative_reward` stays read from `observation` because it is *not* excluded from the serialized observation dict and lives there correctly.

**Alternative considered:** Modify `SentinelObservation.model_dump()` to not exclude reward. Rejected — that would require patching the OpenEnv library or overriding serialization, adding fragility without benefit.

### D2 — Track a rolling offset in the SSE generator

Introduce a local `offset` variable initialized to `0` before the loop, and advance it by the number of lines returned each tick:

```python
async def event_generator():
    offset = 0
    while True:
        lines = runner.get_output_since(offset)
        if lines:
            offset += len(lines)
            for line in lines:
                ...
```

**Alternative considered:** Clear `_output_lines` after each send so there is nothing to re-send. Rejected — history is needed by `/api/run/status` and future reconnect support.

## Risks / Trade-offs

- [Risk] A client that connects mid-run will only receive output from the moment it connects, missing earlier lines → Mitigation: this is the same behavior as most streaming log UIs; a separate "catch-up on connect" endpoint can be added later if needed. The current behavior (replaying everything) is the bug being fixed.
- [Risk] `data.get("reward")` returns `None` for the initial reset observation → Mitigation: the `if _raw_reward is not None` guard in D1 returns `0.0` safely, matching the existing fallback.
