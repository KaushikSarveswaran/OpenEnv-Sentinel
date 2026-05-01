## ADDED Requirements

### Requirement: Run service on separate port
The run execution endpoints SHALL be served by a separate FastAPI application on port 8502 (configurable via `RUN_SERVICE_PORT` env var). The run service SHALL handle: `POST /api/run`, `GET /api/run/stream` (SSE), `POST /api/run/cancel`, `GET /api/run/status`.

#### Scenario: Run service starts on port 8502
- **WHEN** the UI server is started via `python3 -m ui.backend.app`
- **THEN** a run service process SHALL be started on port 8502 alongside the UI service on port 8501

#### Scenario: Run endpoints respond on run service port
- **WHEN** client sends `POST http://localhost:8502/api/run` with a valid model queue
- **THEN** the run service SHALL accept and start execution

#### Scenario: SSE stream on run service port
- **WHEN** client opens `GET http://localhost:8502/api/run/stream`
- **THEN** the SSE connection SHALL be established on the run service origin, leaving UI service connections unaffected

### Requirement: UI service retains history and defaults
The UI service on port 8501 SHALL continue to serve: `GET /api/defaults`, `GET /api/traces`, `GET /api/traces/{filename}`, and static frontend assets. Run endpoints SHALL be removed from the UI service.

#### Scenario: Traces endpoint on UI service
- **WHEN** an SSE stream is active on `:8502` and client calls `GET http://localhost:8501/api/traces`
- **THEN** the request SHALL complete without being blocked by the SSE connection

#### Scenario: Run endpoints removed from UI service
- **WHEN** client calls `POST http://localhost:8501/api/run`
- **THEN** the UI service SHALL return 404 (endpoint does not exist)

### Requirement: Run service includes CORS for UI origin
The run service SHALL include CORS middleware allowing requests from the UI service origin (`http://localhost:8501` and configurable origins).

#### Scenario: Cross-origin run request
- **WHEN** the frontend on `http://localhost:8501` sends `POST http://localhost:8502/api/run`
- **THEN** the run service SHALL include appropriate CORS headers allowing the request

### Requirement: Single entry point starts both services
The `python3 -m ui.backend.app` command SHALL start both the UI service and the run service. The run service SHALL be started as a subprocess.

#### Scenario: Both services start
- **WHEN** user runs `python3 -m ui.backend.app`
- **THEN** both services SHALL be running and accepting connections on their respective ports

#### Scenario: Main process exit stops both
- **WHEN** the main UI service process is terminated
- **THEN** the run service subprocess SHALL also be terminated

### Requirement: Frontend uses separate API base for run endpoints
The frontend SHALL use a separate base URL for run-related API calls (targeting port 8502) and the existing base URL for history/defaults calls (targeting port 8501).

#### Scenario: Run call goes to run service
- **WHEN** user clicks Run in the UI
- **THEN** the `POST /api/run` request SHALL be sent to the run service origin (`:8502`)

#### Scenario: History call goes to UI service
- **WHEN** user navigates to History tab
- **THEN** the `GET /api/traces` request SHALL be sent to the UI service origin (`:8501`)

### Requirement: EventSource visibility workarounds removed
The RunView component SHALL NOT use a `visible` prop, offset-based EventSource reconnection, or visibility-based EventSource lifecycle management. A plain EventSource connection SHALL be used since SSE is on a separate origin.

#### Scenario: Simple EventSource usage
- **WHEN** a run starts and RunView subscribes to SSE
- **THEN** a single EventSource SHALL be created without offset or visibility management

#### Scenario: Tab switch does not affect run or history
- **WHEN** user switches from Run tab to History tab during an active run
- **THEN** History tab SHALL load traces immediately AND the run SHALL continue in the background
