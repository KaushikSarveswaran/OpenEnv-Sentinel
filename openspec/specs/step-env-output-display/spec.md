### Requirement: Display environment tool output in step detail
The `StepDetail` component SHALL render `env_response.tool_output` inline when a step is expanded, immediately after the tool parameters block.

#### Scenario: Tool output is present and short
- **WHEN** a step is expanded and `env_response.tool_output` is 500 characters or fewer
- **THEN** the full tool output SHALL be displayed in a `<pre>` block labelled "Tool Output:" without any truncation or toggle

#### Scenario: Tool output is present and long
- **WHEN** a step is expanded and `env_response.tool_output` exceeds 500 characters
- **THEN** the first 500 characters SHALL be displayed, followed by an expand toggle
- **AND** clicking the toggle SHALL reveal the complete output
- **AND** clicking the toggle again SHALL collapse it back to the truncated view

#### Scenario: Tool output is empty or absent
- **WHEN** a step is expanded and `env_response.tool_output` is an empty string or absent
- **THEN** the tool output section SHALL NOT be rendered

### Requirement: Display environment error text inline
The `StepDetail` component SHALL render `env_response.error` as a formatted error block when the step is expanded and an error is present.

#### Scenario: Error is present
- **WHEN** a step is expanded and `env_response.error` is a non-empty string
- **THEN** the full error text SHALL be displayed in a styled error block within the step detail

#### Scenario: No error present
- **WHEN** a step is expanded and `env_response.error` is empty or absent
- **THEN** no error text block SHALL be rendered (the existing error badge in the step-brief is sufficient)
