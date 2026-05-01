## ADDED Requirements

### Requirement: Raw output renders as a structured coloured block when valid JSON
The `StepDetail` component SHALL replace the plain `<pre class="raw-output">` text block with a `LlmResponseBlock` component that parses `raw_output` and renders each field individually with colour and structure. The stored trace data and all API responses SHALL remain unchanged.

#### Scenario: reasoning field is coloured amber
- **WHEN** `raw_output` is valid JSON and contains a `reasoning` key
- **THEN** an amber label reading "reasoning" SHALL be displayed, followed by the reasoning text in a block below it

#### Scenario: tool_name field is coloured with the accent colour
- **WHEN** `raw_output` is valid JSON and contains a `tool_name` key
- **THEN** a pill/badge with the tool name SHALL be rendered using the accent colour (`--accent`)

#### Scenario: parameters render as key-value rows
- **WHEN** `raw_output` is valid JSON and contains a `parameters` key whose value is an object
- **THEN** each parameter SHALL be displayed as a row with the key in muted colour and the value in bright text

#### Scenario: unknown extra fields render generically
- **WHEN** `raw_output` is valid JSON and contains keys other than `reasoning`, `tool_name`, `parameters`
- **THEN** each extra key SHALL be rendered as a neutral-coloured label with its string/JSON value beside it

#### Scenario: field order is reasoning first, then tool_name, then parameters, then extras
- **WHEN** `raw_output` is valid JSON with multiple fields
- **THEN** fields SHALL appear in the order: `reasoning`, `tool_name`, `parameters`, then any remaining keys

#### Scenario: Non-JSON raw output falls back to plain pre block
- **WHEN** `raw_output` cannot be parsed as JSON (plain text, malformed JSON, markdown fences)
- **THEN** the component SHALL fall back to rendering the original string in a `<pre class="raw-output">` element unchanged

#### Scenario: Empty raw output
- **WHEN** `raw_output` is an empty string
- **THEN** the component SHALL render nothing (or an empty container) with no error

#### Scenario: Trace data is unmodified
- **WHEN** the trace viewer renders a step with JSON raw output
- **THEN** the value stored in the trace JSON file and returned by the `/api/traces/{filename}` endpoint SHALL remain the original compact string
