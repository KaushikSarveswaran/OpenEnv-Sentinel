## Context

The Sentinel UI currently runs a single FastAPI server on port 8501 that serves:
- Static frontend assets
- History/traces API (`GET /api/traces`, `GET /api/traces/{filename}`)
- Defaults API (`GET /api/defaults`)
- Run execution API (`POST /api/run`, `GET /api/run/stream` SSE, `POST /api/run/cancel`, `GET /api/run/status`)

The SSE stream for run output occupies a persistent HTTP/1.1 connection. Browsers limit concurrent connections to 6 per origin, so the SSE stream reduces available connections to 5. In practice this blocks the `/api/traces` fetch when switching tabs.

## Goals / Non-Goals

**Goals:**
- Isolate SSE streaming to its own origin so it cannot block UI/history API calls
- Keep SSE for log streaming (it works well for this use case)
- Simplify frontend code by removing EventSource lifecycle workarounds
- Single `python3 -m ui.backend.app` command starts both services

**Non-Goals:**
- Service discovery or inter-service communication (they share filesystem for traces, no RPC needed)
- Docker/container orchestration
- HTTP/2 upgrade (would also fix the connection limit, but adds TLS complexity for local dev)

## Decisions

### 1. Two FastAPI apps, two ports

**Choice**: UI service on `:8501` (defaults, traces, static files), Run service on `:8502` (run, stream, cancel, status).

**Rationale**: Simplest way to get two origins. Both are lightweight FastAPI apps. The run service is stateful (holds subprocess + output buffer) so it's a natural boundary.

**Alternatives considered**:
- HTTP/2: Multiplexes over one TCP connection, fixing the limit. But requires TLS certificates for local dev, adding setup friction.
- WebSocket: Still holds a connection, same origin problem.
- Polling: Works but loses real-time log streaming that SSE provides well.

### 2. Frontend uses two API base URLs

**Choice**: `api.ts` exports two base URLs — `/api` for UI service (proxied to `:8501`) and `/run-api` for run service (proxied to `:8502`). In production (built static), the frontend calls the ports directly.

**Rationale**: During Vite dev, the proxy handles CORS. In production, the static files are served from `:8501` and the frontend uses absolute URLs for the run service.

### 3. Main entry point starts both services

**Choice**: `python3 -m ui.backend.app` spawns the run service as a subprocess on `:8502`, then starts the UI service on `:8501`.

**Rationale**: Single command to start everything. The run service is a child process — when the main process exits, both stop.

### 4. Shared config module

**Choice**: Both services import from `ui.backend.config` for `PROJECT_ROOT`, `TRACE_DIR`, etc. The run service adds `RUN_SERVICE_PORT`.

**Rationale**: Avoids duplication. Both services need the same paths.

## Risks / Trade-offs

- [Two ports to manage] → Mitigated by single entry point that starts both. User only needs to know `:8501`.
- [CORS required for cross-origin run API calls] → Run service includes CORS middleware allowing `:8501` origin.
- [Slightly more code] → Net reduction once SSE workarounds are removed (~50 lines of EventSource lifecycle code deleted, ~30 lines of new run_service.py added).
