## ADDED Requirements

### Requirement: Trigger inference run
The system SHALL provide a "Run" button that starts `inference.py` as a subprocess with the selected provider and model configuration injected via environment variables.

#### Scenario: User starts a run
- **WHEN** the user has at least one model configured and clicks "Run"
- **THEN** `inference.py` is launched as a subprocess with the appropriate env vars (e.g., `AZURE_OPENAI_API_KEY`, `MODEL_NAME`, `API_BASE_URL`) set for the selected model
- **AND** the Run button is disabled until the current run completes or is cancelled

#### Scenario: No models configured
- **WHEN** the user clicks "Run" with no models in the queue
- **THEN** the system displays a validation error prompting the user to add at least one model

### Requirement: Live output streaming
The system SHALL stream `inference.py` stdout and stderr to the UI in real time using Server-Sent Events.

#### Scenario: Output streams during run
- **WHEN** a run is in progress
- **THEN** the console panel in the UI displays stdout/stderr lines as they are emitted by the subprocess

#### Scenario: Run completes
- **WHEN** `inference.py` finishes (exit code 0)
- **THEN** the console shows the final output including scores and trace file path
- **AND** the run status changes to "Completed"

#### Scenario: Run fails
- **WHEN** `inference.py` exits with a non-zero code
- **THEN** the console shows the error output
- **AND** the run status changes to "Failed" with the exit code

### Requirement: Cancel running inference
The system SHALL allow the user to cancel a running inference by sending SIGTERM to the subprocess.

#### Scenario: User cancels a run
- **WHEN** a run is in progress and the user clicks "Cancel"
- **THEN** the subprocess is terminated via SIGTERM
- **AND** the run status changes to "Cancelled"

### Requirement: Sequential multi-model execution
When multiple models are queued, the system SHALL run them sequentially, advancing to the next model after the current one completes (or fails/is cancelled).

#### Scenario: Multiple models in queue
- **WHEN** the user queues 3 models and clicks "Run"
- **THEN** the system runs model 1, waits for completion, then runs model 2, then model 3
- **AND** progress is shown (e.g., "Running 2/3")
