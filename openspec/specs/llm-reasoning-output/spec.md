## ADDED Requirements

### Requirement: LLM JSON output includes optional reasoning field
When `openenv.yaml` has `inference.enable_reasoning: true`, inference SHALL instruct the LLM to include a `"reasoning"` key in every JSON response. The reasoning SHALL be a plain-text string describing why the agent chose its action. The `reasoning` field SHALL be extracted from the parsed action dict before the action is forwarded to the environment, so the environment protocol is unaffected.

#### Scenario: Reasoning present in LLM output
- **WHEN** `inference.enable_reasoning: true` and the LLM includes `"reasoning": "<text>"` in its JSON response
- **THEN** `parse_action` SHALL return the action dict with `tool_name` and `parameters` only (no `reasoning` key)
- **AND** the extracted reasoning text SHALL be stored separately for tracing

#### Scenario: Reasoning absent in LLM output
- **WHEN** `inference.enable_reasoning: true` but the LLM omits the `"reasoning"` key
- **THEN** reasoning SHALL be treated as `None` and the action SHALL still be parsed normally

#### Scenario: enable_reasoning disabled
- **WHEN** `inference.enable_reasoning: false` (default)
- **THEN** the SYSTEM_PROMPT SHALL NOT mention a reasoning field
- **AND** `reasoning` SHALL be `None` for all steps

### Requirement: Reasoning stored in per-step trace
Each step record in the explainability trace JSON SHALL include a `reasoning` field inside `llm_call`. When reasoning is captured it SHALL be the full extracted string; when absent it SHALL be `null`.

#### Scenario: Reasoning captured in trace
- **WHEN** the LLM returns reasoning text and `inference.enable_reasoning: true`
- **THEN** the trace step's `llm_call.reasoning` SHALL be the extracted string

#### Scenario: No reasoning in trace
- **WHEN** `inference.enable_reasoning: false` or the LLM omits the field
- **THEN** the trace step's `llm_call.reasoning` SHALL be `null`

### Requirement: Reasoning optionally passed back to LLM next turn
When `inference.pass_reasoning_to_llm: true` and `inference.enable_reasoning: true` and reasoning was captured at step N, inference SHALL prepend the reasoning text (labelled `"Your prior reasoning: ..."`) to the user message at step N+1. When `pass_reasoning_to_llm: false` (default), reasoning SHALL NOT be included in any subsequent message. `pass_reasoning_to_llm` has no effect when `enable_reasoning: false` — since no reasoning is ever captured the pass-through is permanently a no-op and inference SHALL log a startup warning.

#### Scenario: Pass-through enabled with reasoning present
- **WHEN** `inference.pass_reasoning_to_llm: true` and `inference.enable_reasoning: true` and step N produced a non-empty reasoning string
- **THEN** the user message at step N+1 SHALL begin with `"Your prior reasoning: <text>"` before the tool output

#### Scenario: Pass-through enabled but no reasoning captured at step
- **WHEN** `inference.pass_reasoning_to_llm: true` but reasoning at step N is `None` or empty
- **THEN** the user message at step N+1 SHALL NOT include any reasoning prefix

#### Scenario: Pass-through disabled
- **WHEN** `inference.pass_reasoning_to_llm: false`
- **THEN** reasoning SHALL never appear in any user message regardless of whether it was captured

#### Scenario: pass_reasoning_to_llm true but enable_reasoning false
- **WHEN** `inference.enable_reasoning: false` and `inference.pass_reasoning_to_llm: true`
- **THEN** inference SHALL emit a startup warning that `pass_reasoning_to_llm` has no effect
- **AND** no reasoning SHALL ever be captured or passed back (reasoning is always `None`)
- **AND** the agent loop SHALL proceed normally as if `pass_reasoning_to_llm` were also false

### Requirement: Config read from openenv.yaml
Inference SHALL read `enable_reasoning` and `pass_reasoning_to_llm` from the `inference:` section of `openenv.yaml` at startup. Missing keys SHALL default to `false`. An absent `inference:` block SHALL be treated as all defaults.

#### Scenario: openenv.yaml has inference block
- **WHEN** `openenv.yaml` contains `inference: {enable_reasoning: true, pass_reasoning_to_llm: false}`
- **THEN** inference SHALL run with reasoning enabled and pass-through disabled

#### Scenario: openenv.yaml has no inference block
- **WHEN** `openenv.yaml` has no `inference:` key
- **THEN** both flags SHALL default to `false` and inference SHALL run with no change in behaviour
