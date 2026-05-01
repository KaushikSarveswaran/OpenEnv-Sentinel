## ADDED Requirements

### Requirement: Reward field is always a float
`SentinelObservation.reward` SHALL be typed as `float` with a default value of `0.0`. It SHALL NOT be `Optional[float]` or `None` at any point in an episode.

#### Scenario: Reset observation reward value
- **WHEN** the environment is reset and returns the initial `SentinelObservation`
- **THEN** the `reward` field SHALL be `0.0` (float), not `None`

#### Scenario: Step observation reward value
- **WHEN** the environment processes a step and returns a `SentinelObservation`
- **THEN** the `reward` field SHALL be a non-null float reflecting the per-step reward computed by `compute_step_reward`

#### Scenario: Serialization
- **WHEN** a `SentinelObservation` is serialized to JSON (e.g., via `model_dump()`)
- **THEN** `reward` SHALL serialize as a JSON number, never as `null`
