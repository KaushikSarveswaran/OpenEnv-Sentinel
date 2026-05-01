## Context

OpenEnv-Sentinel is an RL environment for SRE incident triage. The current workflow is entirely CLI-driven: users configure environment variables in `.env`, run `inference.py` from the terminal, and inspect raw `explainability_trace_*.json` files manually. There is already a FastAPI server (`server/app.py`) that hosts the environment at `localhost:8000`.

The project supports three LLM providers: HuggingFace (default), OpenRouter, and Azure OpenAI — each with distinct configuration variables. Comparing model performance requires editing `.env` and re-running, with no side-by-side comparison capability.

## Goals / Non-Goals

**Goals:**
- Provide a local web UI to configure providers/models, trigger inference runs, and view results
- Support Azure OpenAI and OpenRouter as selectable providers with sensible defaults and the ability to add custom models
- Stream inference output to the UI in real time
- Render explainability trace JSON in a structured, browsable viewer
- Keep the existing `inference.py` and CLI workflow fully functional and unchanged

**Non-Goals:**
- Cloud deployment or multi-user access — this is a single-user local development tool
- Modifying the RL environment server or its API contract
- Building a production-grade frontend with auth, persistence, or database
- Supporting HuggingFace as a selectable provider in the UI (it remains available via CLI)

## Decisions

### 1. Separate UI backend vs. extending existing server

**Decision**: Create a new lightweight FastAPI app under `ui/` rather than extending `server/app.py`.

**Rationale**: The existing server is the RL environment — it must stay clean and focused. The UI backend has orthogonal concerns (process management, file listing, SSE streaming). Coupling them would create startup ordering issues (UI needs to manage the env server lifecycle). A separate app also lets users run the UI without conflicting with the env server port.

**Alternatives considered**: Extending `server/app.py` — rejected because it mixes concerns and the env server is meant to be a standalone component.

### 2. Frontend technology

**Decision**: Use React with Vite, bundled as static assets served by the UI backend.

**Rationale**: React provides component-based structure suitable for the model selector, run console, and trace viewer. Vite gives fast dev iteration. Static bundling means no Node.js runtime needed in production — just `pip install` and run.

**Alternatives considered**: Plain HTML+JS (simpler but harder to maintain interactive components like the trace tree), Streamlit (too opinionated for custom layouts, poor streaming support).

### 3. Running inference

**Decision**: Invoke `inference.py` as a subprocess with environment variables injected per-run. Stream stdout/stderr back via Server-Sent Events (SSE).

**Rationale**: Subprocess isolation prevents model configuration from leaking between runs. SSE is simpler than WebSockets for unidirectional streaming and natively supported by browsers. Environment variables are the existing configuration mechanism for `inference.py` — no code changes needed.

**Alternatives considered**: Importing `inference.py` as a module (would require refactoring its global state), WebSockets for streaming (unnecessary complexity for one-way data).

### 4. Model configuration UX

**Decision**: Provider tabs (Azure OpenAI, OpenRouter). Clicking a provider reveals its configuration form with defaults pre-populated. Users can add multiple models per provider to queue runs.

**Rationale**: Matches the user's mental model — pick a provider, configure it, add models. Defaults reduce friction (Azure shows the configured deployment, OpenRouter shows a popular default). Multiple models per provider enable batch comparison without re-configuration.

### 5. Trace storage and access

**Decision**: Read existing `explainability_trace_*.json` files from the project root. No additional database or storage layer.

**Rationale**: `inference.py` already writes traces to the project root with timestamped filenames. The UI just needs to list and serve them. Adding a database for a local dev tool is unnecessary overhead.

## Risks / Trade-offs

- **[Subprocess management complexity]** → Mitigated by allowing only one run at a time and using proper process group termination. A "cancel run" button will send SIGTERM.
- **[Port conflicts]** → The UI backend will default to port 8501 (distinct from env server 8000). Configurable via env var.
- **[Large trace files]** → Some traces can be large (many steps × full message history). Mitigated by lazy-loading step details in the viewer and paginating the step list.
- **[Frontend build step adds complexity]** → Mitigated by bundling pre-built assets in the package. Dev mode uses Vite's HMR for fast iteration.
