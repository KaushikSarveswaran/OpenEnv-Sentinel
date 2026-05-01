## 1. Update StepDetail Component

- [x] 1.1 Add `showFullOutput` boolean state to `StepDetail` in `ui/frontend/src/views/TraceViewer.tsx`
- [x] 1.2 Render a "Tool Output:" labelled `<pre>` block displaying `env_response.tool_output` (truncated to 500 chars) when the field is non-empty
- [x] 1.3 Add a "Show full output / Hide" toggle button that reveals/collapses the full `tool_output` string when it exceeds 500 characters
- [x] 1.4 Move the `env_response.error` text rendering from being badge-only to also show the full error string as a styled block within the expanded step detail

## 2. Styling

- [x] 2.1 Add a `.tool-output` CSS class in `ui/frontend/src/App.css` (or the relevant stylesheet) for the tool output `<pre>` block — style to visually distinguish it from the LLM raw output block
- [x] 2.2 Verify the existing `.step-error` class sufficiently styles the inline error text; add styles if needed

## 3. Build & Verify

- [x] 3.1 Run `npm run build` in `ui/frontend/` and confirm no TypeScript or build errors
- [x] 3.2 Manually open a trace in the History tab, expand a step, and confirm `tool_output` is visible inline
- [x] 3.3 Confirm that steps with long tool outputs show the truncated view with the expand toggle working correctly
- [x] 3.4 Confirm that steps with errors show the error text inline when expanded
- [x] 3.5 Confirm that steps with empty `tool_output` do not render the tool output section
