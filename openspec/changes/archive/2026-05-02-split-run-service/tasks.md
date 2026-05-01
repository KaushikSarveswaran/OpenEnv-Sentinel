## 1. Backend — Create run service

- [x] 1.1 Add `RUN_SERVICE_PORT` (default 8502) to `ui/backend/config.py`
- [x] 1.2 Create `ui/backend/run_service.py` — new FastAPI app with CORS, importing runner and run-related routes
- [x] 1.3 Move run endpoints from `routes.py` to `run_service.py`: `POST /api/run`, `GET /api/run/stream`, `POST /api/run/cancel`, `GET /api/run/status`
- [x] 1.4 Remove run endpoints and runner import from `routes.py` (keep defaults + traces only)
- [x] 1.5 Remove `StreamingResponse` import from `routes.py` if no longer used

## 2. Backend — Single entry point

- [x] 2.1 Update `app.py` `main()` to spawn `run_service.py` as a subprocess on `RUN_SERVICE_PORT` before starting UI service
- [x] 2.2 Add subprocess cleanup — terminate run service child process on exit (atexit or signal handler)

## 3. Frontend — Split API base URLs

- [x] 3.1 Update `api.ts` — add `RUN_API` base URL pointing to `:8502`, keep `API` for `:8501`
- [x] 3.2 Update `startRun()`, `cancelRun()`, `fetchRunStatus()`, `streamRunOutput()` to use `RUN_API` base
- [x] 3.3 Update `vite.config.ts` — add dev proxy `/run-api` → `http://localhost:8502`

## 4. Frontend — Simplify RunView

- [x] 4.1 Remove `visible` prop from RunView interface and all visibility-based `useEffect` hooks
- [x] 4.2 Remove `linesRef`, `statusRef`, offset tracking — use simple EventSource with `useEffect` cleanup on unmount
- [x] 4.3 Update `App.tsx` — remove `visible` prop from `<RunView>`

## 5. Build, verify, document

- [x] 5.1 Run `npx tsc --noEmit` — verify TypeScript compiles
- [x] 5.2 Run `npm run build` — rebuild static assets
- [x] 5.3 Start both services, run inference, switch to History tab during run, confirm traces load immediately
- [x] 5.4 Update `UI_GUIDE.md` with two-service architecture and why it was adopted
