## Why

Running `inference.py` today requires manually setting environment variables, executing from the CLI, and opening raw JSON trace files to review results. Comparing model performance across Azure OpenAI and OpenRouter providers means editing `.env`, re-running, and mentally diff-ing JSON files. A web UI would let users configure providers/models, trigger runs, and inspect explainability traces visually — all in one place.

## What Changes

- Add a web-based dashboard (served locally) that wraps `inference.py` execution
- Provider selection panel: click "Azure OpenAI" or "OpenRouter" to reveal provider-specific config with sensible defaults (e.g., default deployment for Azure, default model for OpenRouter)
- Ability to add multiple models within each provider and queue runs across them
- Live run status / progress output streamed to the UI while inference is executing
- JSON trace viewer that renders `explainability_trace_*.json` files in a structured, navigable format (metadata summary, per-task breakdown, step-by-step drill-down)
- Run history: list of past runs with model name, scores, and timestamp; click to view the trace

## Capabilities

### New Capabilities
- `inference-dashboard`: Web UI shell — layout, navigation, and local dev server for the dashboard
- `model-selection`: Provider/model configuration panel with Azure OpenAI and OpenRouter support, default models, and ability to add custom models
- `run-execution`: Trigger inference runs from the UI, stream stdout/stderr, and capture results
- `trace-viewer`: Render explainability trace JSON in a structured, browsable view

### Modified Capabilities
<!-- No existing specs to modify -->

## Impact

- **New code**: A frontend app (likely under `ui/`) and a thin backend API (or extension of the existing FastAPI server) to broker runs
- **Dependencies**: A JS/TS frontend framework (e.g., React/Vite or plain HTML+JS) and possibly additional Python deps for process management
- **Existing code**: `inference.py` will be invoked as a subprocess or imported; its interface stays unchanged
- **APIs**: New local HTTP endpoints to list models, start a run, stream output, and fetch/list traces
- **No breaking changes** to the existing CLI or environment server
