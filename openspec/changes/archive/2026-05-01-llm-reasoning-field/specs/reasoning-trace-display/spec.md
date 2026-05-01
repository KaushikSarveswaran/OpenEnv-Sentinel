## ADDED Requirements

### Requirement: StepDetail renders reasoning when present
The `StepDetail` component in the trace viewer SHALL display a collapsible "Reasoning" block when `step.llm_call.reasoning` is a non-empty string. The block SHALL be collapsed by default and toggled by a button.

#### Scenario: Reasoning present and collapsed by default
- **WHEN** a step is expanded and `llm_call.reasoning` is a non-empty string
- **THEN** a "Show Reasoning" button SHALL appear in `StepDetail`
- **AND** the reasoning text SHALL be hidden until the button is clicked

#### Scenario: Reasoning expanded
- **WHEN** the user clicks "Show Reasoning"
- **THEN** the full reasoning text SHALL be rendered in a `<pre>` block labeled "Reasoning:"
- **AND** the button label SHALL change to "Hide Reasoning"

#### Scenario: Reasoning absent
- **WHEN** `llm_call.reasoning` is `null`, `undefined`, or an empty string
- **THEN** no reasoning block or toggle button SHALL be rendered

### Requirement: TraceStep type includes reasoning field
The `TraceStep` TypeScript type SHALL include `reasoning: string | null` on the `llm_call` object so the frontend correctly types trace data from the API.

#### Scenario: Trace with reasoning deserializes correctly
- **WHEN** the API returns a trace step with `llm_call.reasoning` set to a string
- **THEN** TypeScript SHALL not produce a type error when accessing `step.llm_call.reasoning`

#### Scenario: Trace without reasoning deserializes correctly
- **WHEN** the API returns a trace step with `llm_call.reasoning` as `null` or absent
- **THEN** `step.llm_call.reasoning` SHALL be `null` and no rendering errors SHALL occur
