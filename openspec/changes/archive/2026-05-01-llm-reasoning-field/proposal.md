## Why

The LLM agent's decision-making is a black box — traces show what tool was called but not why. Adding an optional `reasoning` field to the JSON output lets the model express its chain-of-thought alongside each action, making traces interpretable and enabling experiments where that reasoning is fed back into the next turn (chain-of-thought prompting).

## What Changes

- **`openenv.yaml`**: Add an `inference:` block with two boolean fields: `enable_reasoning: false` and `pass_reasoning_to_llm: false`.
- **`inference.py`**: Read `enable_reasoning` and `pass_reasoning_to_llm` from `openenv.yaml` at startup. When `enable_reasoning` is true, the SYSTEM_PROMPT instructs the LLM to include a `"reasoning": "<text>"` field in every JSON response alongside `tool_name` and `parameters`. `pass_reasoning_to_llm` has no effect unless `enable_reasoning` is also true — if no reasoning is ever captured there is nothing to pass back.
- **`inference.py`**: Update `parse_action` to extract and strip `reasoning` from the parsed action dict before forwarding the action to the environment; store it in the trace.
- **`inference.py`**: Extend the per-step trace record with `reasoning: str | None` inside `llm_call`.
- **`ui/backend/models_config.py`**: Surface `enable_reasoning` and `pass_reasoning_to_llm` in `get_defaults()` by reading from `openenv.yaml` so the UI can display them.
- **`ui/frontend/src/types.ts`**: Add `reasoning?: string | null` to `TraceStep.llm_call`.
- **`ui/frontend/src/views/TraceViewer.tsx`**: Render reasoning in `StepDetail` when present — collapsible block labeled "Reasoning".
- **Frontend rebuild**: Run `vite build` to update `ui/backend/static/`.

## Capabilities

### New Capabilities
- `llm-reasoning-output`: LLM JSON responses MAY include a `reasoning` field; inference extracts it, strips it from the action, stores it in the trace, and conditionally echoes it back in the next turn.
- `reasoning-trace-display`: The trace UI SHALL render per-step reasoning in the `StepDetail` component when present.

### Modified Capabilities

## Impact

- `openenv.yaml` — new `inference:` section with `enable_reasoning` and `pass_reasoning_to_llm` fields
- `inference.py` — reads `openenv.yaml`, `SYSTEM_PROMPT` conditional, `parse_action`, per-step trace dict, `build_tool_response_prompt`
- `ui/backend/models_config.py` — `get_defaults()` exposes two new keys from `openenv.yaml`
- `ui/frontend/src/types.ts` — `TraceStep` type extended
- `ui/frontend/src/views/TraceViewer.tsx` — `StepDetail` renders reasoning block
- `ui/backend/static/` — must be rebuilt from frontend source
