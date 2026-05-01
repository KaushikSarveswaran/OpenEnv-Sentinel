## Why

The trace viewer currently dumps `raw_output` — the verbatim LLM response — into a `<pre>` block. Because the LLM responds with JSON, this means every step shows a compact unreadable blob. Structured, coloured rendering of each field (reasoning, tool name, parameters) makes debugging agent behaviour significantly easier without changing any stored data.

## What Changes

- The `<pre class="raw-output">` block inside "Show Messages" is replaced with a new `LlmResponseBlock` component.
- When `raw_output` is valid JSON, the component renders each field with colour and structure:
  - `reasoning` — amber label + prose text block (if present in the JSON)
  - `tool_name` — accent-coloured pill/badge
  - `parameters` — key-value rows (muted key, bright value)
  - Any unknown fields — neutral label + value
- When `raw_output` cannot be parsed as JSON, the component falls back to the original `<pre>` raw text display.
- No changes to trace JSON files, API responses, `inference.py`, or backend code.

## Capabilities

### New Capabilities
- `raw-output-pretty-print`: Replace the raw LLM output `<pre>` block with a structured, coloured component that renders JSON fields individually.

### Modified Capabilities
<!-- No existing spec requirements change — this is purely a UI rendering improvement. -->

## Impact

- **Modified files**: `ui/frontend/src/views/TraceViewer.tsx`, `ui/frontend/src/App.css`
- **No backend changes**, no API contract changes, no trace format changes
- Frontend must be rebuilt (`npm run build`) and static assets updated after change
