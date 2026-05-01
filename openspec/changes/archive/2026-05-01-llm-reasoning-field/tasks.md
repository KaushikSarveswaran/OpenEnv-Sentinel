## 1. Add Reasoning Config to `openenv.yaml` and `inference.py`

- [x] 1.1 In `openenv.yaml`, add an `inference:` block with `enable_reasoning: false` and `pass_reasoning_to_llm: false`
- [x] 1.2 In `inference.py`, add a `_load_inference_config()` helper that reads `openenv.yaml` with `yaml.safe_load`, extracts the `inference:` dict, and returns it (defaulting to `{}` if absent or unreadable)
- [x] 1.3 Set module-level `ENABLE_REASONING = bool(_INF_CFG.get("enable_reasoning", False))` and `PASS_REASONING_TO_LLM = bool(_INF_CFG.get("pass_reasoning_to_llm", False))`
- [x] 1.4 After loading config, if `PASS_REASONING_TO_LLM` is true and `ENABLE_REASONING` is false, print a startup warning: `"WARNING: pass_reasoning_to_llm has no effect when enable_reasoning is false"`
- [x] 1.5 When `ENABLE_REASONING` is true, append a sentence to `SYSTEM_PROMPT` instructing the LLM to include `"reasoning": "<explanation>"` as the first key in every JSON response

## 2. Update `parse_action` to Extract Reasoning

- [x] 2.1 Change `parse_action` signature to return `tuple[dict | None, str | None]` — `(action_dict, reasoning)`
- [x] 2.2 Inside `parse_action`, after a successful parse, call `action_dict.pop("reasoning", None)` and return it as the second element; return `(None, None)` on parse failure
- [x] 2.3 Update all call sites of `parse_action` in `inference.py` to unpack both return values

## 3. Thread Reasoning Through the Inference Loop

- [x] 3.1 Store the extracted `reasoning` string from each successful LLM parse into a local variable `step_reasoning`
- [x] 3.2 In `build_tool_response_prompt`, add an optional `prior_reasoning: str | None = None` parameter; when `PASS_REASONING_TO_LLM` is true and `prior_reasoning` is non-empty, prepend `"Your prior reasoning: <text>\n\n"` before the tool output block
- [x] 3.3 Pass `step_reasoning` to `build_tool_response_prompt` when appending the next user message in the loop

## 4. Record Reasoning in the Trace

- [x] 4.1 Add `"reasoning": step_reasoning` to the `llm_call` dict inside the per-step `trace_steps.append(...)` call (value is the string or `None`)

## 5. Surface Reasoning Config in `models_config.py` Defaults

- [x] 5.1 In `get_defaults()`, read `openenv.yaml` (reuse or import the same helper from `inference.py` or duplicate a minimal read) and add `"enable_reasoning"` and `"pass_reasoning_to_llm"` under an `"inference"` key in the returned dict so the UI frontend can read and display the current config values

## 6. Update Frontend TypeScript Types

- [x] 6.1 In `ui/frontend/src/types.ts`, add `reasoning: string | null;` to the `llm_call` field of the `TraceStep` interface

## 7. Render Reasoning in `TraceViewer.tsx`

- [x] 7.1 In `StepDetail`, add `const [showReasoning, setShowReasoning] = useState(false)` state
- [x] 7.2 After the `step-params` block, render a "Show Reasoning" / "Hide Reasoning" toggle button and a collapsible `<pre className="reasoning-output">` block when `step.llm_call.reasoning` is non-empty
- [x] 7.3 Add `.reasoning-output` CSS to `ui/frontend/src/index.css` (or wherever styles live) styled similarly to `.tool-output`

## 8. Build Frontend and Update Static Assets

- [x] 8.1 Run `cd ui/frontend && npm run build` (or equivalent) to produce updated files in `ui/backend/static/`
- [x] 8.2 Confirm the compiled `ui/backend/static/assets/index-*.js` references the new reasoning block

## 9. Verify End-to-End

- [x] 9.1 Run `pytest` from the project root and confirm all tests pass
- [x] 9.2 Start the environment server and the UI backend, open a saved trace in the browser, and confirm steps with `reasoning: null` show no reasoning block and steps with reasoning text show the collapsible block
