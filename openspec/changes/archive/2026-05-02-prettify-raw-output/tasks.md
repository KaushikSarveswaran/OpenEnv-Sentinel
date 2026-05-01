## 1. CSS — New Coloured Classes

- [x] 1.1 Add `.llm-resp-block` container class in `App.css` (dark background, border-left accent, padding, `max-height: 300px`, `overflow-y: auto`, `border-radius`)
- [x] 1.2 Add `.llm-field` row wrapper, `.llm-label` base pill style, `.llm-label-reasoning` (amber / `--yellow`), `.llm-label-tool` (accent / `--accent`), `.llm-label-generic` (muted)
- [x] 1.3 Add `.llm-value` for plain field values, `.llm-param-row` row, `.llm-param-key` (muted mono), `.llm-param-val` (bright mono)
- [x] 1.4 Add `.llm-reasoning-text` block — same style as `.reasoning-output` (dark bg, amber left-border, `pre-wrap`, scrollable)

## 2. Component — LlmResponseBlock

- [x] 2.1 Add `LlmResponseBlock({ raw }: { raw: string })` function component in `TraceViewer.tsx`
- [x] 2.2 Parse `raw` with `JSON.parse`; if it throws, fall back to `<pre className="raw-output">{raw}</pre>`
- [x] 2.3 Render `reasoning` field first: amber `.llm-label-reasoning` pill + `.llm-reasoning-text` block below
- [x] 2.4 Render `tool_name` field: `.llm-label-tool` accent pill with the tool name as text
- [x] 2.5 Render `parameters` field: iterate keys and render each as a `.llm-param-row` with `.llm-param-key` and `.llm-param-val`; stringify non-string values
- [x] 2.6 Render any remaining unknown fields as a `.llm-label-generic` pill + `.llm-value` beside it
- [x] 2.7 Return an empty fragment when `raw` is empty

## 3. Swap in StepDetail

- [x] 3.1 Replace `<pre className="raw-output">{step.llm_call.raw_output}</pre>` with `<LlmResponseBlock raw={step.llm_call.raw_output} />`

## 4. Build and Verify

- [x] 4.1 Run `npm run build` in `ui/frontend` and confirm it completes without TypeScript errors
- [x] 4.2 Confirm the compiled `ui/backend/static/assets/index-*.js` reflects the change
- [x] 4.3 Load the trace viewer in the browser, expand a step's "Show Messages" section, and verify: reasoning shows amber, tool_name shows accent pill, parameters render as rows, non-JSON output falls back to raw `<pre>`
