## Why

The Sentinel UI runs all API endpoints on a single origin (`localhost:8501`). The SSE stream for live run output (`GET /api/run/stream`) holds a persistent HTTP/1.1 connection, consuming one of the browser's 6 per-origin connection slots. When a user switches to the History tab during an active run, `GET /api/traces` competes for the remaining connections and may block — causing "Loading traces..." to hang indefinitely.

Rather than removing SSE (which works well for streaming logs) or adding complex EventSource lifecycle management, the fix is architectural: split run execution into its own service on a separate port. Each origin gets an independent pool of 6 browser connections, so SSE on one origin cannot block fetches to the other.

## What Changes

- **Split run endpoints into a separate service** (`run_service.py`) on port 8502, handling `POST /run`, `GET /run/stream` (SSE), `POST /run/cancel`, `GET /run/status`
- **Keep UI service** (`app.py`) on port 8501, handling `GET /defaults`, `GET /traces`, `GET /traces/{filename}`, and static file serving
- **Update frontend** to call run endpoints on `localhost:8502` and history/defaults on `localhost:8501`
- **Remove SSE workarounds** — drop `visible` prop, EventSource visibility lifecycle, offset-based reconnection from RunView
- **Add architecture doc** explaining why the split was made

## Capabilities

### New Capabilities
- `run-service-split`: Separate run execution service on its own port, with SSE streaming isolated from the main UI service

### Modified Capabilities

## Impact

- `ui/backend/routes.py` — Remove run endpoints (POST /run, GET /run/stream, POST /run/cancel, GET /run/status); keep defaults + traces
- `ui/backend/run_service.py` — New FastAPI app with run endpoints + runner, on port 8502
- `ui/backend/app.py` — No longer imports runner
- `ui/frontend/src/api.ts` — Run API calls go to `:8502`, history calls stay on `:8501`
- `ui/frontend/src/views/RunView.tsx` — Simplify: remove `visible` prop, remove offset reconnection, use plain EventSource
- `ui/frontend/src/App.tsx` — Remove `visible` prop from RunView
- `ui/frontend/vite.config.ts` — Add proxy for `/run-api` → `:8502`
