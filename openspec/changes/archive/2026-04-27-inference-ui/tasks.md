## 1. Project Scaffolding

- [x] 1.1 Create `ui/` directory with backend (`ui/backend/`) and frontend (`ui/frontend/`) sub-directories
- [x] 1.2 Initialize Vite + React + TypeScript project in `ui/frontend/`
- [x] 1.3 Create `ui/backend/app.py` FastAPI application with CORS and static file serving
- [x] 1.4 Add Python dependencies (`fastapi`, `uvicorn`, `sse-starlette`) to `pyproject.toml` or `ui/backend/requirements.txt`
- [x] 1.5 Add a CLI entry point (e.g., `python -m ui.backend.app`) to start the UI server on port 8501 (configurable via `UI_PORT`)

## 2. Model Selection API & UI

- [x] 2.1 Create `ui/backend/models_config.py` — data models for provider configs (AzureOpenAI, OpenRouter) with defaults loaded from env vars
- [x] 2.2 Add `GET /api/defaults` endpoint returning default provider configs from environment
- [x] 2.3 Build provider tabs component (`ProviderTabs`) — clickable Azure OpenAI and OpenRouter cards
- [x] 2.4 Build Azure OpenAI config form with fields: endpoint, deployment, API key, API version (pre-populated from env)
- [x] 2.5 Build OpenRouter config form with fields: API key, model name, site URL, site name (pre-populated with defaults)
- [x] 2.6 Build "Add Model" button and model queue list component with remove capability
- [x] 2.7 Support adding models from both providers into a single run queue

## 3. Run Execution Backend

- [x] 3.1 Create `ui/backend/runner.py` — subprocess manager that launches `inference.py` with injected env vars
- [x] 3.2 Add `POST /api/run` endpoint accepting a list of model configs, launching sequential subprocess runs
- [x] 3.3 Add `GET /api/run/stream` SSE endpoint streaming stdout/stderr from the active subprocess
- [x] 3.4 Add `POST /api/run/cancel` endpoint sending SIGTERM to the active subprocess
- [x] 3.5 Add `GET /api/run/status` endpoint returning current run state (idle, running, model index, total models)

## 4. Run Execution UI

- [x] 4.1 Build the Run view layout with model queue summary, Run/Cancel buttons, and console output panel
- [x] 4.2 Connect Run button to `POST /api/run` and subscribe to SSE stream for live output
- [x] 4.3 Display real-time stdout/stderr in a scrollable console component with auto-scroll
- [x] 4.4 Show run progress indicator (e.g., "Running 2/3") for multi-model queues
- [x] 4.5 Handle run completion, failure, and cancellation states in the UI

## 5. Trace Viewer Backend

- [x] 5.1 Add `GET /api/traces` endpoint listing all `explainability_trace_*.json` files with parsed metadata (model, score, timestamp)
- [x] 5.2 Add `GET /api/traces/{filename}` endpoint returning full trace JSON content

## 6. Trace Viewer UI

- [x] 6.1 Build History view listing past runs (model name, average score, timestamp, task count) sorted by timestamp descending
- [x] 6.2 Build Trace Viewer layout with metadata summary header
- [x] 6.3 Build per-task collapsible sections showing task ID, incident summary, final score, steps, LLM calls
- [x] 6.4 Build step-by-step timeline within each task — tool name, parameters, reward, error, latency, token usage
- [x] 6.5 Add expandable "Show messages" panel per step displaying `messages_sent` and `raw_output`
- [x] 6.6 Build score comparison table for multi-run selection from History view

## 7. Integration & Polish

- [x] 7.1 Add sidebar/tab navigation component wiring Run, History, and Trace Viewer views
- [x] 7.2 Configure Vite build to output static assets to `ui/backend/static/` for production serving
- [x] 7.3 Add empty-state handling for History (no traces) and Run (no models configured) views
- [x] 7.4 Test end-to-end: start UI server, configure models, run inference, view trace

## 8. Post-archive fixes

- [x] 8.1 Load `.env` secrets as defaults via `python-dotenv` in `config.py`
- [x] 8.2 Fix RunView unmounting on tab switch — keep mounted with `display: none` instead of conditional render
- [x] 8.3 Fix browser connection exhaustion — close EventSource when RunView hidden, reconnect with offset on return
- [x] 8.4 Add `offset` query param to `GET /api/run/stream` SSE endpoint for resume support
- [x] 8.5 Add `visible` prop to RunView for EventSource lifecycle management
- [x] 8.6 Fix runner.py env var leaking — clear ALL provider env vars before setting the selected provider's vars
- [x] 8.7 Create `UI_GUIDE.md` documentation
