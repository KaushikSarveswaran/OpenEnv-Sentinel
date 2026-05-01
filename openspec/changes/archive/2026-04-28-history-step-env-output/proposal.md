## Why

When reviewing a trace in the History tab, each step currently shows the LLM's tool call and reward, but the environment's response (`tool_output`) is hidden. To understand what happened in a step, users must expand the *next* step's messages and search the prompt for the prior result — a tedious, error-prone workflow. Surfacing `tool_output` directly on the step that produced it makes trace debugging significantly faster.

## What Changes

- Each step card in the `TraceViewer` step timeline now displays the environment's `tool_output` inline, below the tool call parameters.
- The output is rendered in a scrollable `<pre>` block, truncated with an expand/collapse toggle for long outputs.
- An `env_response.error` message (already shown as a badge) is also shown inline as formatted error text when the step is expanded.

## Capabilities

### New Capabilities

- `step-env-output-display`: Inline display of `env_response.tool_output` (and errors) within each expanded step card in the trace step timeline.

### Modified Capabilities

(none — no existing spec files exist)

## Impact

- **`ui/frontend/src/views/TraceViewer.tsx`**: `StepDetail` component updated to render `env_response.tool_output`.
- **`ui/frontend/src/types.ts`**: No changes required; `tool_output` is already in `TraceStep.env_response`.
- **Backend / API**: No changes required; `tool_output` is already included in the trace JSON.
- **CSS (`App.css` or component styles)**: Minor additions for the new `tool-output` block styling.
