# Sentinel UI — Dashboard Guide

Web dashboard for running inference against the OpenEnv-Sentinel environment, viewing explainability traces, and comparing model scores.

---

## Quick Start

### 1. Start the environment server

```bash
.venv/bin/python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### 2. Start the UI and run services

```bash
python3 -m ui.backend.app
```

This single command starts **both** services:
- UI service on **http://localhost:8501** (open this in your browser)
- Run service on **http://localhost:8502** (started automatically as a subprocess)

### 3. Environment variables (optional)

Create a `.env` file in the project root. The UI auto-loads it and pre-populates forms:

```env
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_API_VERSION=2025-04-01-preview

OpenRouter_API=sk-or-v1-...
```

| Variable | Purpose |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment/model name |
| `AZURE_OPENAI_API_KEY` | Azure API key |
| `AZURE_OPENAI_API_VERSION` | API version (default: `2025-04-01-preview`) |
| `OpenRouter_API` | OpenRouter API key (also accepts `OPENROUTER_API_KEY`) |
| `ENV_URL` | Environment server URL (default: `http://localhost:8000`) |
| `UI_PORT` | UI server port (default: `8501`) |
| `RUN_SERVICE_PORT` | Run service port (default: `8502`) |

---

## Views

### Run View

The main view for configuring and launching inference runs.

**Provider Selection**

- **Azure OpenAI** — Fill in endpoint, deployment name, API key, and API version. Fields are pre-populated from `.env`.
- **OpenRouter** — Select a model from the dropdown of 12 curated free models, or toggle "Custom" to enter any model ID. API key is pre-populated from `.env`.

**Model Queue**

- Click **Add Model** to add the configured model to the run queue.
- Mix providers freely — e.g., one Azure model and two OpenRouter models in the same queue.
- Remove models from the queue by clicking the × button.

**Running**

- Click **Run** to execute inference sequentially for each queued model.
- Live console output streams in real-time via SSE.
- Progress indicator shows "Running 1/3" etc. for multi-model queues.
- Click **Cancel** to stop the current run (sends SIGTERM).
- Switching tabs does not block — run SSE streams on a separate service (port 8502) so History loads instantly.

**Free Models Available**

| Model | Context |
|---|---|
| Google: Gemma 4 31B | 262K |
| Google: Gemma 4 26B A4B | 262K |
| Qwen: Qwen3 Coder 480B A35B | 262K |
| Qwen: Qwen3 Next 80B A3B | 262K |
| NVIDIA: Nemotron 3 Super | 262K |
| inclusionAI: Ling-2.6-1T | 262K |
| inclusionAI: Ling-2.6-flash | 262K |
| Meta: Llama 3.3 70B Instruct | 65K |
| OpenAI: gpt-oss-120b | 131K |
| OpenAI: gpt-oss-20b | 131K |
| Nous: Hermes 3 405B Instruct | 131K |
| MiniMax: MiniMax M2.5 | 196K |

### History View

Lists all completed runs from the `traces/` folder, sorted by most recent.

- Each row shows: model name, average score, task count, timestamp.
- Click a row to open the detailed Trace Viewer.
- Use checkboxes to select 2+ runs, then click **Compare** for side-by-side scores.

### Trace Viewer

Detailed breakdown of a single inference run.

- **Metadata** — Model name, average score, total tasks, timestamp.
- **Tasks** — Collapsible sections per task showing incident summary, final score, and step count.
- **Steps** — Timeline within each task: tool name, parameters, reward, errors, latency, token usage.
- **Messages** — Expandable "Show Messages" panel per step with the full `messages_sent` and `raw_output`.

### Compare View

Side-by-side score comparison of selected runs.

- Per-task scores across models in a table.
- Average scores highlighted with color coding (green > 0.5, yellow > 0.1, red ≤ 0.1).

---

## URL Navigation

The UI uses **hash-based routing** — the URL fragment updates automatically as you move between views. This means:

- Bookmarking or sharing a URL lands directly on the correct view.
- The browser Back/Forward buttons work as expected.
- No server-side routing configuration is needed.

| View | URL |
|---|---|
| Run | `http://localhost:8501/#` |
| History | `http://localhost:8501/#history` |
| Trace Viewer | `http://localhost:8501/#trace` |
| Compare | `http://localhost:8501/#compare` |

> **Note:** Refreshing the page on `/#history`, `/#trace`, or `/#compare` restores the correct view. For `/#trace` and `/#compare` the selected trace/files come from in-memory state, so refreshing those will redirect back to History.

---

## Architecture

The UI uses a **two-service architecture** to avoid HTTP/1.1 per-origin connection limits. Browsers cap 6 simultaneous connections per origin — an SSE stream holds one permanently, which can block other API calls (like loading traces). Splitting run execution onto a separate port gives SSE its own origin, so History and other views load instantly even during a run.

**Why two ports instead of two endpoints on one server?**  
If both endpoints lived on `:8501`, the browser would still see them as the same origin and share the same connection pool. The SSE stream would still compete with trace fetches. Port separation is the cheapest way to get two independent connection pools without needing TLS (required for HTTP/2) or abandoning real-time streaming.

**How the frontend addresses both services:**  
`api.ts` uses two base URLs. UI calls use a relative path (`/api`) so they always go to whatever host served the page. Run calls use an absolute URL (`http://localhost:8502`) so they explicitly target the run service's origin regardless of where the page was loaded from. This is what makes the connection pool split effective.

```
ui/
├── backend/
│   ├── app.py            # UI service (:8501) — static files, defaults, traces
│   ├── run_service.py    # Run service (:8502) — run, stream SSE, cancel, status
│   ├── config.py         # Shared constants, .env loading
│   ├── models_config.py  # Provider models, defaults
│   ├── routes.py         # UI API endpoints (defaults, traces)
│   ├── runner.py         # Subprocess manager for inference.py
│   └── static/           # Built frontend assets
└── frontend/
    └── src/
        ├── App.tsx
        ├── api.ts         # API client (two base URLs)
        ├── types.ts       # TypeScript types
        ├── components/    # ModelSelection, ConsoleOutput
        └── views/         # RunView, HistoryView, TraceViewer, CompareView
```

**UI Service (`:8501`) — API Endpoints**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/defaults` | Provider defaults from `.env` |
| `GET` | `/api/traces` | List all traces with metadata |
| `GET` | `/api/traces/{filename}` | Full trace JSON |

**Run Service (`:8502`) — API Endpoints**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/run` | Start inference with model queue |
| `GET` | `/api/run/stream` | SSE stream of live output |
| `GET` | `/api/run/status` | Current run state |
| `POST` | `/api/run/cancel` | Cancel active run |

---

## Development

### Frontend dev server (hot reload)

```bash
cd ui/frontend
npm run dev
```

Proxies `/api` to `http://localhost:8501`. The run service calls use the absolute URL `http://localhost:8502` directly and do not need proxying.

### Rebuild static assets

```bash
cd ui/frontend
npm run build
```

Outputs to `ui/backend/static/`. Restart the backend to serve the new build.

### Traces

All trace files are stored in the `traces/` folder at the project root. The folder is auto-created on first run.
