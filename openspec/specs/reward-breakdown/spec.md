## ADDED Requirements

### Requirement: Reward breakdown data structure
The grading layer SHALL produce a structured `RewardBreakdown` object for every step alongside the scalar reward. The breakdown SHALL contain:
- `components`: an ordered list of `RewardComponent` items, each with a `label` (string) and `value` (float).
- `classification`: a single string label describing the dominant reward event — one of `"invalid"`, `"repeated"`, `"relevant"`, `"irrelevant"`.
- `reason`: a human-readable string explaining the reward, e.g. `"relevant tool call (query_logs:auth-service): +0.12, step cost: -0.01"`.

#### Scenario: Relevant tool call breakdown
- **WHEN** `compute_step_reward` is called with a valid, non-repeated, relevant tool call
- **THEN** the returned `RewardBreakdown` SHALL have `classification="relevant"`, a `components` list containing a step-cost entry and a relevant-bonus entry, and a `reason` string that names the tool and service

#### Scenario: Invalid action breakdown
- **WHEN** `compute_step_reward` is called with `is_valid=False`
- **THEN** the returned `RewardBreakdown` SHALL have `classification="invalid"`, components for step cost and invalid penalty, and a `reason` string indicating the action was invalid

#### Scenario: Repeated tool call breakdown
- **WHEN** `compute_step_reward` is called for a call signature already in `previous_calls`
- **THEN** the returned `RewardBreakdown` SHALL have `classification="repeated"` and a `reason` string identifying the repeated signature

#### Scenario: Irrelevant tool call breakdown
- **WHEN** `compute_step_reward` is called with a valid, non-repeated, irrelevant tool call
- **THEN** the returned `RewardBreakdown` SHALL have `classification="irrelevant"` and a `reason` string stating the tool was not in the relevant set

### Requirement: Reward breakdown in trace
The inference layer SHALL write the `reward_breakdown` object from each step into the `env_response` block of the corresponding trace step JSON. The `reward_breakdown` field SHALL contain `components`, `classification`, and `reason`.

#### Scenario: Breakdown present in written trace
- **WHEN** a run completes and the trace JSON is written to disk
- **THEN** each step's `env_response` SHALL contain a `reward_breakdown` object with `classification` and `reason` fields

#### Scenario: Backward compatibility with old traces
- **WHEN** the UI loads a trace file that does not contain `reward_breakdown` in a step's `env_response`
- **THEN** the UI SHALL render the step normally without the breakdown badge, with no error

### Requirement: Reward breakdown displayed in UI trace viewer
The trace viewer's `StepDetail` component SHALL display the reward breakdown for each step. The breakdown SHALL be collapsed by default and expandable on user interaction.

#### Scenario: Collapsed state shows badge
- **WHEN** a step has a `reward_breakdown` in its `env_response`
- **THEN** the step header SHALL show a small interactive badge or button (e.g. "why?") next to the reward value

#### Scenario: Expanded state shows component table and reason
- **WHEN** the user clicks the breakdown badge
- **THEN** the breakdown panel SHALL expand to show: the `reason` string and each `component` (label and value) listed individually

#### Scenario: Missing breakdown hides badge
- **WHEN** a step does not have a `reward_breakdown` (e.g. old trace file)
- **THEN** no breakdown badge SHALL be rendered for that step
