## Context

Each inference step records `raw_output` (the full LLM text) and `parsed_action` (the extracted JSON). There is no structured way for the model to include explanatory text alongside its action — any chain-of-thought gets buried in `raw_output` as unstructured prose. Observers replaying traces cannot easily distinguish the model's rationale from formatting noise.

The agent loop in `inference.py` maintains a multi-turn conversation in `messages`. Each assistant turn currently carries only the raw output; the next user turn carries only the environment response. If the model's prior reasoning is potentially useful for the next step, there is no mechanism to surface it in a structured way.

## Goals / Non-Goals

**Goals:**
- Let the LLM optionally express reasoning as a first-class JSON field alongside every action
- Capture that reasoning in per-step trace records so it is visible in the UI
- Provide a second config flag to echo reasoning back into the conversation for the next turn
- Keep both behaviours off by default so existing runs are unaffected

**Non-Goals:**
- Validating, scoring, or grading the quality of reasoning text
- Storing reasoning separately from the trace (it lives inside the trace JSON)
- Changing the OpenEnv environment protocol — reasoning is stripped before the action is forwarded to the server

## Decisions

### Decision 1: Reasoning lives inside the JSON action object, not as a separate field

The LLM is already instructed to emit a single JSON object. The simplest extension is to allow an extra `"reasoning": "<text>"` key in that same object: `{"reasoning": "...", "tool_name": "...", "parameters": {...}}`. This requires no new parsing strategy — the existing multi-fallback `parse_action` already extracts the object.

`parse_action` is then extended to pop `reasoning` from the dict before returning, so the action forwarded to the environment is unchanged. Reasoning is returned as a second value (or stored on the side).

**Alternative considered:** A separate JSON object or a structured `<think>` tag. Rejected because it requires a new parsing path and changes the prompt contract more extensively.

### Decision 2: Config lives in `openenv.yaml` under an `inference:` block

The project already has `openenv.yaml` as the central config file (spec_version, name, runtime, port). Reasoning flags belong there rather than as env vars because:
- Env vars are ephemeral and per-process; these are persistent agent behaviour settings
- `openenv.yaml` is checked into the repo so settings are version-controlled and reproducible
- The UI runner (`InferenceRunner._build_env`) already reconstructs env vars for subprocesses — adding more env vars there would grow the override list unnecessarily

`inference.py` reads `openenv.yaml` once at startup with PyYAML (`yaml.safe_load`) and extracts the `inference:` key. Defaults are `enable_reasoning: false` and `pass_reasoning_to_llm: false` so existing setups without an `inference:` block are unaffected.

**Alternative considered:** Env vars (as originally designed). Rejected because they are not version-controlled, must be re-set on every new shell, and require the runner to forward them explicitly to subprocesses.

### Decision 3: Pass reasoning back as part of the user message, not as a system message

If `PASS_REASONING_TO_LLM` is true, the reasoning from step N is prepended to the user content at step N+1 in `build_tool_response_prompt`. Using a system message would conflate conversation-level instructions with per-step context. A user message with a label like `"Your prior reasoning: ..."` keeps it scoped to the turn.

**Alternative considered:** Separate assistant-turn message that mirrors reasoning back. Rejected because it doubles the message count and confuses turn ordering.

### Decision 4: Frontend shows reasoning as a collapsible block in `StepDetail`

Reasoning can be long. A collapsible `<details>` / toggle pattern (matching the existing "Show Messages" / "Show full output" pattern in the UI) avoids cluttering the default step view. It appears only when `llm_call.reasoning` is non-null and non-empty.

The frontend is compiled to `ui/backend/static/` — any change requires a `vite build` step.

## Risks / Trade-offs

- **Token cost** → Reasoning increases prompt+completion token count. Both flags default `false`. Mitigation: defaults are in `openenv.yaml` so the trade-off is self-documenting in the config file.
- **`pass_reasoning_to_llm: true` with `enable_reasoning: false`** → No reasoning is ever captured, so pass-through is permanently a no-op. This combination is safe but meaningless. Mitigation: `inference.py` emits a startup warning when this combination is detected; the spec explicitly defines the behaviour as a no-op.
- **JSON compliance** → Some models may put `reasoning` as nested JSON or omit it even when asked. The parser must treat a missing key gracefully (`reasoning = action_dict.pop("reasoning", None)`).
- **Stale static build** → If a developer edits the frontend but forgets `vite build`, the UI won't reflect the change. Mitigation: the build step is an explicit task in tasks.md.
- **`PASS_REASONING_TO_LLM` context length** → Long reasoning at every step could bloat the conversation faster than the existing trim logic handles. Mitigation: truncate reasoning in the pass-through to a configurable max (e.g. 500 chars), or rely on existing conversation trim (`call_messages[:2] + call_messages[-20:]`).
