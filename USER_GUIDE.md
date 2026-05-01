# OpenEnv-Sentinel — User Guide

Step-by-step guide for running, validating, and deploying the SRE Incident Triage environment.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Local Setup](#2-local-setup)
3. [Running the Server Locally](#3-running-the-server-locally)
4. [Manual Validation — Local Server](#4-manual-validation--local-server)
5. [Docker Build & Validation](#5-docker-build--validation)
6. [Running Inference (LLM Agent)](#6-running-inference-llm-agent)
7. [OpenEnv Validate](#7-openenv-validate)
8. [Deploy to Hugging Face Spaces](#8-deploy-to-hugging-face-spaces)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | ≥ 3.10 | Runtime |
| pip / pipenv | Latest | Dependency management |
| Docker | Latest | Container build & test |
| Git | Latest | Version control, HF push |
| huggingface-cli | Latest | HF Spaces deployment |
| openenv-core CLI | ≥ 0.2.3 | `openenv validate` / `openenv push` |

Install the OpenEnv CLI and Hugging Face CLI:

```bash
pip install openenv-core huggingface-hub[cli]
```

---

## 2. Local Setup

### Option A — pip (quick)

```bash
cd openenv-sentinel
pip install -e ".[dev,inference]"
```

### Option B — pipenv (isolated)

```bash
cd openenv-sentinel
pipenv install --python 3.12
pipenv install -e ".[dev]"
pipenv install openai httpx websockets
pipenv shell
```

All subsequent commands assume you are inside the virtual environment.

---

## 3. Running the Server Locally

Start the FastAPI server on port 8000:

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Verify with:

```bash
curl http://localhost:8000/health
# → {"status":"ok"}

curl http://localhost:8000/schema
# → JSON with action, observation, state schemas
```

---

## 4. Manual Validation — Local Server

With the server running (from step 3), validate the environment in a **second terminal**.

### 4.1 Automated test script

The quickest way to validate all 3 tasks end-to-end:

```bash
pip install websockets httpx   # if not already installed
python test_local.py
```

Expected output:

```
Health: {'status': 'ok'}
Schema: action fields=['tool_name', 'parameters']

==================================================
TASK 1
==================================================
  Reset OK: CRITICAL: payment-api returning HTTP 500 errors...
  Step 1 (status payment-api): reward=0.11
  Step 2 (logs payment-api): reward=0.11
  Resolution: score=0.75, done=True
  State: final_score=1.0, root_cause_correct=True, recommendation_correct=True

... (Tasks 2 & 3 similar) ...

✅ ALL TESTS PASSED
```

### 4.2 Manual cURL validation (HTTP endpoints)

> **Note:** HTTP endpoints are stateless — each request creates a fresh environment
> instance. Use these for single-shot checks only. For multi-step episodes, use
> the WebSocket endpoint (section 4.3).

**Health check:**

```bash
curl http://localhost:8000/health
```

**Schema check:**

```bash
curl http://localhost:8000/schema | python -m json.tool
```

**Reset (single-shot):**

```bash
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1}'
```

### 4.3 Manual WebSocket validation (stateful sessions)

Multi-step episodes require WebSocket because the server maintains session state
across messages. Install `websocat` or use Python:

**Using Python interactively:**

```python
import asyncio, json, websockets

async def manual_test():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        # 1. Reset to Task 1
        await ws.send(json.dumps({"type": "reset", "data": {"task_id": 1}}))
        resp = json.loads(await ws.recv())
        print("Reset:", json.dumps(resp["data"]["observation"]["incident_summary"]))

        # 2. Call a diagnostic tool
        await ws.send(json.dumps({
            "type": "step",
            "data": {
                "tool_name": "get_service_status",
                "parameters": {"service": "payment-api"}
            }
        }))
        resp = json.loads(await ws.recv())
        print("Step 1:", resp["data"]["observation"]["tool_output"][:200])

        # 3. Submit resolution
        await ws.send(json.dumps({
            "type": "step",
            "data": {
                "tool_name": "submit_resolution",
                "parameters": {
                    "root_cause": "Missing DB_CONNECTION_STRING after v2.3.1 deploy",
                    "affected_service": "payment-api",
                    "recommendation": "Rollback to v2.3.0 or set the env var"
                }
            }
        }))
        resp = json.loads(await ws.recv())
        print("Done:", resp["data"]["done"], "Score:", resp["data"]["reward"])

        # 4. Get final state
        await ws.send(json.dumps({"type": "state"}))
        resp = json.loads(await ws.recv())
        print("Final score:", resp["data"]["final_score"])

asyncio.run(manual_test())
```

**Using websocat (CLI tool):**

```bash
brew install websocat   # macOS
websocat ws://localhost:8000/ws
```

Then type JSON messages line by line:

```json
{"type": "reset", "data": {"task_id": 1}}
{"type": "step", "data": {"tool_name": "get_service_status", "parameters": {"service": "payment-api"}}}
{"type": "step", "data": {"tool_name": "submit_resolution", "parameters": {"root_cause": "Missing DB_CONNECTION_STRING", "affected_service": "payment-api", "recommendation": "Rollback to v2.3.0"}}}
{"type": "state"}
```

### 4.4 What to check

| Check | Expected |
|---|---|
| `/health` returns 200 | `{"status": "ok"}` |
| `/schema` returns action/observation/state schemas | Three top-level keys with JSON Schema properties |
| Reset with `task_id` 1, 2, 3 | Returns `incident_summary`, `available_tools` (7 tools), `done: false` |
| Diagnostic tool steps | Returns `tool_output` (non-empty), per-step `reward` |
| `submit_resolution` | Sets `done: true`, returns graded `reward` |
| State after resolution | `final_score` between 0.0–1.0, `root_cause_correct` bool |
| All 3 tasks produce scores > 0.0 with good resolutions | Task 1 ≈ 1.0, Task 2 ≈ 1.0, Task 3 ≈ 1.0 (with ideal answers) |

---

## 5. Docker Build & Validation

### 5.1 Build the image

```bash
docker build -t sentinel-env:latest -f server/Dockerfile .
```

### 5.2 Run the container

```bash
docker run -p 8000:8000 sentinel-env:latest
```

The server starts on port 8000 inside the container, mapped to your host.

### 5.3 Validate against the container

Once the container is running, all the same validation steps from section 4 work:

```bash
# Health check
curl http://localhost:8000/health

# Run the automated test suite
python test_local.py

# Or run inference against the containerised server
ENV_URL=http://localhost:8000 python inference.py
```

### 5.4 Docker — useful commands

```bash
# Build with no cache (clean rebuild)
docker build --no-cache -t sentinel-env:latest -f server/Dockerfile .

# Run in background
docker run -d --name sentinel -p 8000:8000 sentinel-env:latest

# View logs
docker logs -f sentinel

# Stop and remove
docker stop sentinel && docker rm sentinel

# Check image size (should be < 500MB)
docker images sentinel-env
```

---

## 6. Running Inference (LLM Agent)

The inference script drives an LLM through all 3 tasks via WebSocket.

This section is a practical local activation flow for:
- Activating the RL environment server
- Activating an LLM API provider
- Running inference across multiple models

### 6.1 Understand the two endpoints

- `ENV_URL` points to the Sentinel RL environment server (local FastAPI/WebSocket app)
- `API_BASE_URL` points to the LLM provider endpoint (HF router, OpenAI, etc.)

These are different systems and both must be configured correctly.

### 6.2 Terminal A — activate Python env and start the RL environment

```bash
cd openenv-sentinel
source .venv/bin/activate

# Install inference deps if needed
pip install openai websockets

# Start RL environment server
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

In a second shell, verify:

```bash
curl http://localhost:8000/health
# expected: {"status":"ok"}
```

### 6.3 Terminal B — activate Python env and configure LLM provider

```bash
cd openenv-sentinel
source .venv/bin/activate
export ENV_URL=http://localhost:8000
```

Choose exactly one provider profile below.

#### Option A — Hugging Face Router (default)

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=openai/gpt-oss-120b:novita
export HF_TOKEN=hf_...

# Optional compatibility alias
export API_KEY="$HF_TOKEN"
```

#### Option B — OpenAI API

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o
export API_KEY=sk-...

# Prevent stale HF credentials from being used accidentally
unset HF_TOKEN
```

#### Option C — OpenRouter

```bash
export API_BASE_URL=https://openrouter.ai/api/v1
export MODEL_NAME=openai/gpt-4o-mini
export API_KEY=sk-or-...

# Optional aliases if your key is stored under OPENROUTER_API_KEY
export API_KEY="${OPENROUTER_API_KEY:-$API_KEY}"

# Prevent stale HF credentials from being used accidentally
unset HF_TOKEN
```

#### Option D — Azure OpenAI

```bash
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_API_KEY=your-azure-key
export MODEL_NAME=your-deployment-name
export AZURE_OPENAI_API_VERSION=2025-04-01-preview

# Optional: avoid conflicts with non-Azure vars
unset API_BASE_URL
unset API_KEY
unset HF_TOKEN
```

Notes:
- When Azure variables are set, `inference.py` uses the Azure client.
- Otherwise it uses `OpenAI(base_url=API_BASE_URL, api_key=...)`, covering HF router, OpenAI, and OpenRouter.

### 6.4 Preflight checks before running inference

```bash
# RL environment reachable?
curl -s http://localhost:8000/health

# Required credentials present?
if [[ -n "$AZURE_OPENAI_API_KEY" ]]; then
    echo "Using Azure OpenAI"
elif [[ -n "$API_KEY" || -n "$HF_TOKEN" ]]; then
    echo "Using OpenAI-compatible endpoint"
else
    echo "Missing LLM credentials (set API_KEY or HF_TOKEN or AZURE_OPENAI_API_KEY)"
fi
```

### 6.5 Run local inference

```bash
python inference.py
```

Expected shape of output:

```
Using LLM API: ... / model=...
Environment URL: http://localhost:8000

==================================================
Running Task 1...
==================================================
...
Task 1: <score>

==================================================
Running Task 2...
==================================================
...
Task 2: <score>

==================================================
Running Task 3...
==================================================
...
Task 3: <score>

==================================================
Task 1: <score>
Task 2: <score>
Task 3: <score>
Average: <score>
==================================================
```

The script also writes an explainability trace file:

```text
explainability_trace_YYYYMMDD_HHMMSS.json
```

### 6.6 Run across multiple models (same provider)

Use one provider config, then sweep models:

```bash
for model in \
    openai/gpt-oss-120b:novita \
    meta-llama/Llama-3.3-70B-Instruct \
    mistralai/Mixtral-8x7B-Instruct-v0.1
do
    export MODEL_NAME="$model"
    echo "Running model: $MODEL_NAME"
    python inference.py | tee "run_${MODEL_NAME//\//_}.log"
done
```

### 6.7 Switch providers cleanly

Before switching provider families, clear conflicting env vars:

```bash
unset AZURE_OPENAI_ENDPOINT AZURE_OPENAI_API_KEY AZURE_OPENAI_API_VERSION
unset API_BASE_URL API_KEY HF_TOKEN
```

Then apply exactly one provider profile from section 6.3.

### 6.8 Inference against a remote HF Space

```bash
# HF model via HF router
export ENV_URL=https://your-username-sentinel-env.hf.space
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=openai/gpt-oss-120b:novita
export HF_TOKEN=hf_...
python inference.py

# OpenAI model
export ENV_URL=https://your-username-sentinel-env.hf.space
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o
export API_KEY=sk-...
unset HF_TOKEN
python inference.py

# OpenRouter model
export ENV_URL=https://your-username-sentinel-env.hf.space
export API_BASE_URL=https://openrouter.ai/api/v1
export MODEL_NAME=openai/gpt-4o-mini
export API_KEY=sk-or-...
unset HF_TOKEN
python inference.py

# Azure OpenAI
export ENV_URL=https://your-username-sentinel-env.hf.space
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_API_KEY=your-azure-key
export MODEL_NAME=your-deployment-name
python inference.py
```

---

## 7. OpenEnv Validate

Run the official OpenEnv validation to confirm spec compliance:

```bash
openenv validate
```

This checks:
- `openenv.yaml` manifest is valid
- The app entry point (`server.app:app`) is importable
- A `main()` function exists in the script entry point
- `uv.lock` is present and up to date

If `uv.lock` is missing or stale:

```bash
pip install uv
uv lock
openenv validate
```

---

## 8. Deploy to Hugging Face Spaces

### 8.1 Login to Hugging Face

```bash
huggingface-cli login
# Paste your HF token when prompted (needs write access)
```

### 8.2 Option A — `openenv push` (recommended)

```bash
openenv push
```

This reads `openenv.yaml` and pushes the environment as a Docker Space tagged
with `openenv`.

### 8.3 Option B — Manual HF Spaces deployment

**Step 1: Create the Space**

Go to https://huggingface.co/new-space and create a new Space:

- **Space name:** `sentinel-env` (or any name)
- **SDK:** Docker
- **Hardware:** CPU basic (2 vCPU, 16GB RAM — free tier)
- **Visibility:** Public

**Step 2: Clone the Space repo**

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/sentinel-env hf-space
cd hf-space
```

**Step 3: Copy project files**

```bash
# Copy all source files
cp -r /path/to/openenv-sentinel/{models.py,__init__.py,client.py,inference.py} .
cp -r /path/to/openenv-sentinel/{server,scenarios,tools,grading} .
cp /path/to/openenv-sentinel/openenv.yaml .
cp /path/to/openenv-sentinel/pyproject.toml .
cp /path/to/openenv-sentinel/README.md .

# The Dockerfile must be at the repo root for HF Spaces
cp /path/to/openenv-sentinel/server/Dockerfile .
```

> **Important:** HF Spaces expects `Dockerfile` at the repository root. The
> COPY paths inside the Dockerfile already reference files relative to the
> build context (repo root), so no changes are needed.

**Step 4: Push to HF**

```bash
git add .
git commit -m "Deploy OpenEnv-Sentinel"
git push
```

**Step 5: Verify deployment**

The Space builds automatically. Once running:

```bash
curl https://YOUR_USERNAME-sentinel-env.hf.space/health
# → {"status": "ok"}
```

### 8.4 Verify the deployed Space

```bash
# Health
curl https://YOUR_USERNAME-sentinel-env.hf.space/health

# Schema
curl https://YOUR_USERNAME-sentinel-env.hf.space/schema

# Run test_local.py against the Space (edit BASE_HTTP/BASE_WS in the file)
# Or run inference:
ENV_URL=https://YOUR_USERNAME-sentinel-env.hf.space \
HF_TOKEN=hf_... \
python inference.py
```

### 8.5 HF Spaces tips

- **Cold starts:** Free-tier Spaces sleep after inactivity. First request takes ~30s.
- **Logs:** View build & runtime logs in the Space's "Logs" tab on HF.
- **Environment variables:** Set secrets (like API keys) in Space Settings → Repository secrets.
- **Tags:** Ensure the README frontmatter includes `tags: [openenv]` for hackathon discovery.
- **Port:** The `app_port: 8000` in README frontmatter must match the `EXPOSE` in the Dockerfile.

---

## 9. Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'openenv'` | Run `pip install -e .` or `pip install openenv-core>=0.2.3` |
| `openenv validate` fails with "no main() found" | Ensure `server/app.py` has a `def main()` function and `[project.scripts]` in pyproject.toml |
| `openenv validate` fails with "uv.lock not found" | Run `pip install uv && uv lock` |
| WebSocket connection refused | Server must be running (`uvicorn server.app:app --port 8000`) |
| `Connect call failed ('127.0.0.1', 8000)` in inference | RL environment server is down. Start it in another terminal, then retry |
| HTTP `/step` returns fresh state (not continuing episode) | HTTP endpoints are stateless. Use WebSocket `/ws` for multi-step episodes |
| Docker build fails on `COPY` | Run `docker build` from the project root (not from `server/`) |
| Docker healthcheck failing | Ensure `curl` is installed in the image (the Dockerfile does this) |
| `inference.py` error: "ENV_URL required" | `export ENV_URL=http://localhost:8000` |
| HF Router returns 401 Unauthorized HTML | Set `HF_TOKEN` (or `API_KEY`) in the same shell where inference runs |
| OpenRouter 401/403 | Verify `API_BASE_URL=https://openrouter.ai/api/v1`, `API_KEY`, and model access on your OpenRouter account |
| Azure OpenAI 401 / auth error | Verify `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and that `MODEL_NAME` matches your deployment name |
| HF Space shows "Building" forever | Check the Logs tab for build errors. Common: missing files in COPY |
| HF Space returns 502 | The app hasn't started yet (cold start) or crashed. Check runtime logs |
| Task score is 0.0 | The resolution keywords didn't match. Check grading criteria in HACKATHON_PLAN.md §5 |
| `websockets` not installed | `pip install websockets` |

---

## Quick Reference

```bash
# ── Local development ──
pip install -e ".[dev,inference]"
uvicorn server.app:app --port 8000          # start server
python test_local.py                         # validate all 3 tasks
openenv validate                             # check spec compliance

# ── Docker ──
docker build -t sentinel-env -f server/Dockerfile .
docker run -p 8000:8000 sentinel-env

# ── Inference (HF router — hackathon default) ──
export ENV_URL=http://localhost:8000
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=openai/gpt-oss-120b:novita
export HF_TOKEN=hf_...
python inference.py

# ── Inference (OpenAI) ──
export ENV_URL=http://localhost:8000
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o
export API_KEY=sk-...
python inference.py

# ── Inference (OpenRouter) ──
export ENV_URL=http://localhost:8000
export API_BASE_URL=https://openrouter.ai/api/v1
export MODEL_NAME=openai/gpt-4o-mini
export API_KEY=sk-or-...
python inference.py

# ── Inference (Azure OpenAI) ──
export ENV_URL=http://localhost:8000
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_API_KEY=your-azure-key
export MODEL_NAME=your-deployment-name
python inference.py

# ── Deploy ──
huggingface-cli login
openenv push
```
