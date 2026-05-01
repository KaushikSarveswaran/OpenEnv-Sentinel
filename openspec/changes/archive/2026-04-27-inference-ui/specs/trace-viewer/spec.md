## ADDED Requirements

### Requirement: List past runs
The system SHALL display a history of past inference runs derived from `explainability_trace_*.json` files in the `traces/` folder at the project root. Each entry SHALL show the model name, average score, timestamp, and number of tasks.

#### Scenario: User views run history
- **WHEN** the user navigates to the History view
- **THEN** a list of past runs is displayed, sorted by timestamp descending
- **AND** each entry shows: model name, average score, timestamp, task count

#### Scenario: No traces exist
- **WHEN** no `explainability_trace_*.json` files exist in the `traces/` folder
- **THEN** the History view shows an empty state message

#### Scenario: Traces folder does not exist
- **WHEN** the `traces/` folder does not exist at the project root
- **THEN** the system SHALL create it automatically on startup

### Requirement: Open trace from history
The system SHALL allow the user to click a run in the history list to open its trace in the Trace Viewer.

#### Scenario: User clicks a run entry
- **WHEN** the user clicks on a run in the history list
- **THEN** the Trace Viewer opens with that run's trace data loaded

### Requirement: Trace metadata summary
The Trace Viewer SHALL display a metadata summary at the top showing model name, API base URL, environment URL, timestamp, total tasks, and average score.

#### Scenario: Trace loaded
- **WHEN** a trace file is loaded in the Trace Viewer
- **THEN** the metadata section displays all fields from the trace's `metadata` object

### Requirement: Per-task breakdown
The Trace Viewer SHALL display each task as a collapsible section showing task ID, incident summary, final score, total steps, and total LLM calls.

#### Scenario: User views task details
- **WHEN** a trace is loaded and the user expands a task section
- **THEN** the task's incident summary, final score, step count, and LLM call count are visible

### Requirement: Step-by-step drill-down
Within each task, the Trace Viewer SHALL display a step-by-step timeline. Each step SHALL show the parsed action (tool name + parameters), env response (reward, error), and LLM call metadata (latency, token usage, parse attempts).

#### Scenario: User inspects a step
- **WHEN** the user clicks on a step within a task
- **THEN** the step detail panel shows: tool name, parameters, tool output, reward, cumulative reward, error (if any), LLM latency, token usage, and whether resolution was forced

#### Scenario: User views LLM messages for a step
- **WHEN** the user clicks "Show messages" on a step
- **THEN** the full `messages_sent` array and `raw_output` are displayed in a formatted view

### Requirement: Score comparison across models
When multiple traces are loaded (or selected from history), the Trace Viewer SHALL display a comparison table showing per-task scores and averages side by side.

#### Scenario: User selects two runs for comparison
- **WHEN** the user selects two or more runs from the History view
- **THEN** a comparison table is displayed with columns for each model and rows for each task score plus the average
