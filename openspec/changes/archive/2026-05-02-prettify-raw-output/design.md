## Context

The trace viewer (`ui/frontend/src/views/TraceViewer.tsx`) shows a collapsible "Show Messages" section inside `StepDetail`. At the bottom of that section the LLM's verbatim response is displayed as:

```tsx
<h5>Raw Output</h5>
<pre className="raw-output">{step.llm_call.raw_output}</pre>
```

Because `inference.py` instructs the LLM to respond with a JSON object, the field contains strings like:

```
{"reasoning":"The alert is OOM","tool_name":"query_logs","parameters":{"service":"auth-service"}}
```

Rendering this as a raw string (even indented) makes it hard to scan. The stored trace JSON and all API contracts are unaffected — the only change is how the string is rendered in the browser.

## Goals / Non-Goals

**Goals:**
- Replace the `<pre class="raw-output">` block with a `LlmResponseBlock` component that renders each JSON field with a distinct colour and label
- `reasoning` — amber label, full prose text below it
- `tool_name` — accent-coloured pill
- `parameters` — key/value rows (muted key, bright value)
- Any extra/unknown fields — neutral pill label + string value
- Fall back to the original `<pre>` block when the output cannot be parsed as JSON
- Zero changes to trace storage format, `inference.py`, backend API, or `types.ts`

**Non-Goals:**
- Syntax-highlighted token colouring within values
- Replacing the separately-rendered `step-reasoning` collapsible (that block reads from `step.llm_call.reasoning` extracted by `parse_action`; this is a different, independent display of the raw response before extraction)
- Changing how `messages_sent` are rendered

## Decisions

### Decision 1: New `LlmResponseBlock` sub-component inside TraceViewer.tsx

A small, self-contained function component keeps the change localised and the `StepDetail` render clean. It accepts a single `raw: string` prop, parses it internally, and renders structured markup.

**Alternatives considered:**
- Inline JSX in `StepDetail` — clutters the parent; harder to read and test.
- Shared utility file — overkill for a single call site.

### Decision 2: Field render order — reasoning first, then tool_name, then parameters, then unknowns

Matches the LLM's own instruction to put `reasoning` first. Readers can understand "why" before seeing "what".

### Decision 3: Fallback to `<pre class="raw-output">` on parse error

No regression for edge cases (markdown fences, partial JSON, plain-text retries). The old style block is reused so no extra CSS is needed for the fallback path.

### Decision 4: CSS additions in App.css — new classes, no changes to existing ones

Adding `.llm-resp-block`, `.llm-field`, `.llm-label`, `.llm-label-reasoning`, `.llm-label-tool`, `.llm-value`, `.llm-param-row`, `.llm-param-key`, `.llm-param-val` keeps existing styles untouched and makes the colour intent explicit via class names.

## Risks / Trade-offs

- **LLM outputs partial JSON** → `JSON.parse` throws, component falls back to raw `<pre>`. No regression.
- **Very long reasoning text** → the `.llm-resp-block` container will get a `max-height` + `overflow-y: auto` to contain it, matching the existing `.raw-output` treatment.
- **Unknown extra fields** → rendered generically; no hardcoded field list needed beyond `reasoning`, `tool_name`, `parameters`.

## Migration Plan

1. Add `LlmResponseBlock` component and CSS classes to `TraceViewer.tsx` / `App.css`.
2. Replace `<pre className="raw-output">{step.llm_call.raw_output}</pre>` with `<LlmResponseBlock raw={step.llm_call.raw_output} />`.
3. Run `npm run build` in `ui/frontend` and verify compiled output in `ui/backend/static/`.
4. No backend restart needed; static file is served directly.
