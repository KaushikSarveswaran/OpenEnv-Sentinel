## Why

Two bugs cause degraded inference runs: (1) all per-step rewards appear as `0.00` because `inference.py` reads `reward` from the wrong level of the WebSocket response, and (2) the UI terminal replays the entire run output on every SSE poll because the stream generator always reads from offset 0 instead of tracking where it left off.

## What Changes

- Fix `inference.py` to read `reward` from the top-level `data` dict in the WebSocket response, not from inside `observation` (where it is explicitly excluded by OpenEnv serialization).
- Fix `run_service.py` SSE event generator to track a rolling offset so it only sends new output lines to clients, instead of re-sending the full history on every 0.3-second tick.

## Capabilities

### New Capabilities
<!-- None introduced -->

### Modified Capabilities
- `step-env-output-display`: The terminal output display relies on the SSE stream feeding correctly deduplicated lines; fixing the stream offset directly affects how step output is rendered in the UI.

## Impact

- **`inference.py`**: One-line fix — change `observation.get("reward", 0.0)` to read from `data` (the envelope dict) so actual computed rewards (`+0.11`, `-0.03`, etc.) are captured and logged.
- **`ui/backend/run_service.py`**: One-line fix — introduce a local `offset` variable in `api_run_stream`'s generator so `runner.get_output_since(offset)` is called instead of `runner.get_output_since(0)`, and the offset is advanced after each batch.
- No API, schema, or dependency changes required.
