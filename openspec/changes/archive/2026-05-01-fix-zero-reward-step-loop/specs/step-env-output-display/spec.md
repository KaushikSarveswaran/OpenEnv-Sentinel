## ADDED Requirements

### Requirement: SSE stream sends only new output lines
The run-service SSE endpoint (`GET /api/run/stream`) SHALL deliver each output line exactly once per connected client session. Lines that have already been sent SHALL NOT be re-sent on subsequent ticks.

#### Scenario: New lines arrive while client is connected
- **WHEN** the inference subprocess produces new output lines
- **THEN** only those new lines SHALL be sent to the client on the next SSE tick
- **AND** previously sent lines SHALL NOT be repeated

#### Scenario: No new output since last tick
- **WHEN** no new output lines have been produced since the last SSE tick
- **THEN** only the status event SHALL be emitted; no output events SHALL be sent

#### Scenario: Client connects mid-run
- **WHEN** a client connects to the SSE stream while a run is in progress
- **THEN** the client SHALL receive output lines starting from the point of connection
- **AND** output produced before the connection MAY be absent from the stream for that client

### Requirement: Per-step reward reflects actual computed reward
The inference loop SHALL log each step's reward as the value returned by the environment WebSocket response (`data.reward`), not a default fallback.

#### Scenario: Environment returns a non-zero reward
- **WHEN** the environment returns a non-null `reward` value in the WebSocket step response
- **THEN** the `[STEP]` log line SHALL display that value (e.g., `reward=0.11` or `reward=-0.03`)
- **AND** the reward SHALL be appended to the rewards list used in the `[END]` log line

#### Scenario: Environment returns a null reward
- **WHEN** the environment returns `null` for `reward` (e.g., on reset)
- **THEN** the inference loop SHALL treat it as `0.0` and log `reward=0.00`
