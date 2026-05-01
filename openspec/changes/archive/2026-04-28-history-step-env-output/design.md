## Context

The `TraceViewer` UI (History tab) renders a `StepDetail` component for each step in a task's timeline. A `TraceStep` object carries three sections of data: `llm_call` (messages, raw output, latency, token usage), `parsed_action` (tool name + parameters), and `env_response` (tool_output, reward, cumulative_reward, done, error).

Currently, `StepDetail` renders `parsed_action` and metadata from `llm_call` inline, and gates `llm_call.messages_sent` / `raw_output` behind a "Show Messages" toggle. However, `env_response.tool_output` — the string returned by the environment after executing the tool — is never shown. Users must open the **next** step's "Show Messages" and parse the prompt to find the tool result, which is slow and error-prone.

All the required data is already present in the frontend `TraceStep` type and in the trace JSON files. No backend changes are needed.

## Goals / Non-Goals

**Goals:**
- Display `env_response.tool_output` directly inside the expanded `StepDetail` card, below the tool parameters.
- Truncate long outputs (>500 chars) with an expand/collapse toggle to avoid overwhelming the page.
- Ensure `env_response.error` (already shown as a badge) is also rendered as formatted error text inline when the step is expanded.

**Non-Goals:**
- Changing the trace JSON schema or backend API.
- Adding search or filtering within tool outputs.
- Modifying the `CompareView` or summary tables.
- Changing how `llm_call.messages_sent` / raw output are displayed.

## Decisions

**Decision 1: Render `tool_output` in `StepDetail`, not in `step-brief`**

The `step-brief` row is intentionally compact (one line per step). Full output content belongs in the expanded `StepDetail` view. This keeps the timeline scannable while adding depth on expansion.

*Alternatives considered:* Showing a truncated snippet in `step-brief` — rejected because it adds noise to the timeline and the brief is already crowded with tool name, reward, and error badge.

**Decision 2: Use a collapsible `<pre>` block with a character-length cutoff**

Tool outputs can be multi-line JSON or long log strings. A `<pre>` block preserves whitespace and formatting. A 500-character cutoff (matching the existing message truncation pattern in the component) controls initial height. A "Show full output / Hide" toggle reveals the rest.

*Alternatives considered:* Always showing full output — rejected because some tool outputs are thousands of characters (e.g., log dumps), which would make long traces unreadable.

**Decision 3: Reuse existing toggle pattern from `showMessages`**

`StepDetail` already has a `showMessages` boolean state for the messages/raw-output section. The same pattern (`useState(false)` + a button toggle) is applied to a new `showFullOutput` state for the tool output section. This keeps the component consistent.

**Decision 4: Show `env_response.error` text inline (not just as a badge)**

The badge already signals an error in the brief view. When expanded, the full error string should appear as a styled error block so the user doesn't need to know where else to look.

## Risks / Trade-offs

- **Very large tool outputs** → Mitigation: 500-char truncation + opt-in expand keeps initial render fast.
- **Binary or non-printable output** → Mitigation: Renders safely inside `<pre>`; no parsing attempted.
- **Styling inconsistency** → Mitigation: Reuse existing CSS class patterns (`step-error`, `raw-output`); add a minimal new `.tool-output` class.
