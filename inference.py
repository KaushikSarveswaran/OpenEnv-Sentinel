"""Baseline inference script for OpenEnv-Sentinel.

Drives an LLM agent through all 3 SRE incident triage tasks.

Environment variables:
  ENV_URL          - Sentinel environment server URL (e.g. http://localhost:8000)
  API_BASE_URL     - LLM API base URL (default: https://router.huggingface.co/v1)
  MODEL_NAME       - Model or deployment name (default: openai/gpt-oss-120b:novita)
  HF_TOKEN         - Hugging Face token (used as API key)
    TRACE_DIR        - Directory for trace JSON output (default: traces)
  LOCAL_IMAGE_NAME - Docker image name when using from_docker_image() (optional)

  OpenRouter (used when OPENROUTER_API_KEY is set or API_BASE_URL contains openrouter.ai):
    OPENROUTER_API_KEY       - OpenRouter API key (sk-or-...)
    OPENROUTER_SITE_URL      - Optional: your site URL for OpenRouter rankings
    OPENROUTER_SITE_NAME     - Optional: your site name for OpenRouter rankings

  Azure OpenAI (used when AZURE_OPENAI_API_KEY is set):
    AZURE_OPENAI_ENDPOINT    - Azure endpoint URL
    AZURE_OPENAI_DEPLOYMENT  - Deployment / model name
    AZURE_OPENAI_API_KEY     - Azure API key
    AZURE_OPENAI_API_VERSION - API version (default: 2025-04-01-preview)

Values are also loaded from a .env file in the project root if present.
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    # override=False means shell env vars always win over .env values
    load_dotenv(override=False)
except ImportError:
    pass

import httpx
from openai import AzureOpenAI, OpenAI

# ── configuration ───────────────────────────────────────────────────

# Environment server URL (where the Sentinel env is running)
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")

# LLM configuration (aligned with official OpenEnv inference examples)
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b:novita")
HF_TOKEN = os.getenv("HF_TOKEN")

# Optional — if you use from_docker_image():
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

# Explainability trace output directory
TRACE_DIR = os.getenv("TRACE_DIR", "traces")

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
# Azure takes priority when explicitly configured (endpoint + key)
USE_AZURE = bool(AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT)

# OpenRouter configuration (only when Azure is not active)
# Accepts OPENROUTER_API_KEY or the legacy alias OpenRouter_API
OPENROUTER_API_KEY = (
    os.getenv("OPENROUTER_API_KEY")
    or os.getenv("OpenRouter_API")
)
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "")
USE_OPENROUTER = bool(
    not USE_AZURE
    and (OPENROUTER_API_KEY or "openrouter.ai" in API_BASE_URL)
)

# API key: prefer API_KEY, then OPENROUTER_API_KEY, fall back to HF_TOKEN
API_KEY = (
    os.getenv("API_KEY")
    or OPENROUTER_API_KEY
    or HF_TOKEN
    or os.getenv("OPENAI_API_KEY", "")
)

TASK_TIMEOUT = 360  # 6 minutes per task
MAX_PARSE_RETRIES = 3
MAX_RATELIMIT_RETRIES = 8   # extra retries specifically for 429s (free-tier models)
MAX_COMPLETION_TOKENS = 16384  # reasoning models need room for chain-of-thought

SYSTEM_PROMPT = """You are an expert SRE agent triaging a production incident.
You have access to diagnostic tools. Respond with ONLY a single JSON object — no markdown, no explanation, no extra text.

Available tools:
- get_service_status: {"tool_name": "get_service_status", "parameters": {"service": "<name>"}}
- query_logs: {"tool_name": "query_logs", "parameters": {"service": "<name>", "query": "<text filter, use empty string for all logs>"}}
- query_metrics: {"tool_name": "query_metrics", "parameters": {"service": "<name>", "metric": "<cpu|memory|error_rate|latency|connections>"}}
- get_dependency_map: {"tool_name": "get_dependency_map", "parameters": {"service": "<name or omit for full map>"}}
- consult_runbook: {"tool_name": "consult_runbook", "parameters": {"topic": "<search_topic>"}}
- check_recent_changes: {"tool_name": "check_recent_changes", "parameters": {"service": "<name or omit for all>"}}
- submit_resolution: {"tool_name": "submit_resolution", "parameters": {"root_cause": "<detailed explanation>", "affected_service": "<primary ROOT CAUSE service>", "recommendation": "<specific actionable fix>"}}

INVESTIGATION PLAN — you have only 20 steps total, be extremely efficient:
Step 1: get_dependency_map (no service param) to see full architecture
Step 2: check_recent_changes (no service param) to see all recent deploys and changes
Step 3-4: get_service_status for the UNHEALTHY/DEGRADED services mentioned in the incident
Step 5-6: query_logs for unhealthy services (use "" as query to get all logs)
Step 7-8: query_metrics for the suspicious root-cause service (error_rate, memory, connections)
Step 9: submit_resolution with your findings

CRITICAL RULES:
- The ROOT CAUSE is often UPSTREAM — a dependency of the symptomatic service, not the alerted service itself
- Look for: bad deployments, missing env vars, OOM/memory issues, connection pool exhaustion, long-running queries
- affected_service MUST be the root-cause service, NOT the symptom service
- root_cause must mention specific service names, error types, versions, and technical details
- recommendation must be specific and actionable (e.g. rollback, increase memory limit, kill query, set timeout)
- Do NOT repeat the same tool call — you already have that data
- You MUST call submit_resolution by step 10 at the latest — do not keep investigating
- Respond with ONLY a JSON object. No markdown fences, no explanation."""

FORCE_RESOLUTION_PROMPT = """URGENT: You MUST call submit_resolution NOW. No more investigation.
Synthesize everything you have gathered. Your response MUST be ONLY:
{"tool_name": "submit_resolution", "parameters": {"root_cause": "<detailed with service names, errors, versions>", "affected_service": "<the root cause service>", "recommendation": "<specific fix>"}}
Do NOT call any other tool. Submit NOW."""


# ── action parsing ──────────────────────────────────────────────────

def parse_action(text: str) -> dict | None:
    """Parse LLM output into an action dict with multiple fallbacks."""
    # 1. Direct JSON parse
    try:
        obj = json.loads(text.strip())
        if isinstance(obj, dict) and "tool_name" in obj:
            return obj
    except json.JSONDecodeError:
        pass

    # 2. Extract from markdown code fence
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fence_match:
        try:
            obj = json.loads(fence_match.group(1).strip())
            if isinstance(obj, dict) and "tool_name" in obj:
                return obj
        except json.JSONDecodeError:
            pass

    # 3. Regex: first {...} block
    brace_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if brace_match:
        try:
            obj = json.loads(brace_match.group(0))
            if isinstance(obj, dict) and "tool_name" in obj:
                return obj
        except json.JSONDecodeError:
            pass

    return None


# ── history management ──────────────────────────────────────────────

def build_initial_prompt(observation: dict) -> str:
    """Build the first user prompt from the reset observation."""
    parts = []
    parts.append(f"INCIDENT: {observation.get('incident_summary', '')}")

    tool_descs = observation.get("tool_descriptions")
    if tool_descs:
        parts.append("\n--- AVAILABLE TOOL PARAMETERS ---")
        for tool, meta in tool_descs.items():
            parts.append(f"  {tool}: {json.dumps(meta)}")

    parts.append(
        f"\nStep {observation.get('step_number', 0)}/{observation.get('max_steps', 20)}"
    )
    parts.append("\nBegin your investigation. Respond with your first action as JSON:")
    return "\n".join(parts)


def build_tool_response_prompt(observation: dict) -> str:
    """Build a follow-up user prompt after a tool call."""
    parts = []

    tool_output = observation.get("tool_output", "")
    if tool_output:
        parts.append(f"Tool output:\n{tool_output}")

    if observation.get("last_action_error"):
        parts.append(f"\n⚠ ERROR: {observation['last_action_error']}")

    step_num = observation.get("step_number", 0)
    max_steps = observation.get("max_steps", 20)
    parts.append(
        f"\nStep {step_num}/{max_steps} | "
        f"Cumulative reward: {observation.get('cumulative_reward', 0.0):.2f}"
    )

    # Add urgency nudges based on step progress
    if step_num >= max_steps - 5:
        parts.append("\n⚠⚠ CRITICAL: You MUST call submit_resolution NOW! No more investigation!")
    elif step_num >= max_steps - 8:
        parts.append("\n⚠ WARNING: Submit your resolution NOW. Call submit_resolution with your best analysis.")
    elif step_num >= max_steps - 12:
        parts.append("\nNote: Start forming your resolution. You should submit within the next 2-3 steps.")

    parts.append("\nRespond with your next action as JSON:")
    return "\n".join(parts)


# ── main loop ───────────────────────────────────────────────────────

async def run_task(task_id: int, base_url: str, client: OpenAI) -> dict:
    """Run a single task against the environment via WebSocket.

    Returns dict with keys: score (float), trace (dict with task-level explainability data).
    """
    import websockets

    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = ws_url.rstrip("/") + "/ws"

    async with websockets.connect(ws_url, ping_interval=120, ping_timeout=300) as ws:
        # Reset
        await ws.send(json.dumps({"type": "reset", "data": {"task_id": task_id}}))
        resp = json.loads(await ws.recv())
        data = resp["data"]
        observation = data.get("observation", data)
        done = data.get("done", False)

        # [START] — mandatory structured log
        print(f"[START] task=task_{task_id} env=sentinel_env model={MODEL_NAME}")

        incident_summary = observation.get("incident_summary", "")
        trace_steps: list[dict] = []
        total_llm_calls = 0

        # Build multi-turn conversation
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_initial_prompt(observation)},
        ]
        final_score = 1e-3
        local_step = 0  # track client-side loop iterations
        rewards_list: list[str] = []  # collect per-step rewards for [END] line

        while not done:
            local_step += 1
            step_num = observation.get("step_number", local_step)
            max_steps = observation.get("max_steps", 20)

            # Safety: break if we've looped too many times without env advancing
            if local_step > max_steps + 10:
                print(f"  Exceeded max loop iterations ({local_step}), breaking", flush=True)
                break

            print(f"  Step {step_num} (iter {local_step}): calling LLM...", flush=True)

            # Force resolution when nearing step limit
            force_resolution = step_num >= max_steps - 8
            if force_resolution:
                print(f"  Step {step_num}: FORCING resolution submission", flush=True)
                # Add force prompt as an additional system nudge in the conversation
                force_msg = {"role": "system", "content": FORCE_RESOLUTION_PROMPT}
                call_messages = messages + [force_msg]
            else:
                call_messages = messages

            # Trim conversation if too long (keep system + first user + last 20 messages)
            if len(call_messages) > 30:
                call_messages = call_messages[:2] + call_messages[-20:]

            # Snapshot messages sent to LLM (deep copy for trace)
            messages_snapshot = [dict(m) for m in call_messages]

            # Try to get a valid action from the LLM
            action_dict = None
            raw = ""
            token_usage = None
            llm_latency = 0.0
            parse_attempts = 0
            rl_attempt = 0  # separate counter for rate-limit retries
            for attempt in range(MAX_PARSE_RETRIES + MAX_RATELIMIT_RETRIES):
                parse_attempts = min(attempt + 1, MAX_PARSE_RETRIES)
                total_llm_calls += 1
                t0 = time.time()
                try:
                    # Run sync LLM call in a thread so the event loop can
                    # still handle WebSocket pings during long reasoning calls
                    response = await asyncio.to_thread(
                        client.chat.completions.create,
                        model=MODEL_NAME,
                        messages=call_messages,
                        max_completion_tokens=MAX_COMPLETION_TOKENS,
                    )
                    llm_latency = round(time.time() - t0, 3)
                    raw = response.choices[0].message.content or ""
                    if response.usage:
                        token_usage = {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens,
                        }
                    action_dict = parse_action(raw)
                    if action_dict:
                        # Store the assistant response in conversation
                        messages.append({"role": "assistant", "content": raw})
                        print(f"  Step {step_num}: action={action_dict.get('tool_name', '?')}", flush=True)
                        break
                    else:
                        print(f"  Step {step_num}: parse failed (attempt {attempt + 1}), raw={raw[:200]}", flush=True)
                        # On parse failure, add a nudge and retry
                        if attempt < MAX_PARSE_RETRIES - 1:
                            call_messages = call_messages + [
                                {"role": "assistant", "content": raw},
                                {"role": "user", "content": "That was not valid JSON. Respond with ONLY a JSON object like {\"tool_name\": \"...\", \"parameters\": {...}}"},
                            ]
                except Exception as e:
                    llm_latency = round(time.time() - t0, 3)
                    err_str = str(e)
                    # Back off on rate-limit errors so free-tier models can recover
                    if "429" in err_str or "rate limit" in err_str.lower():
                        rl_attempt += 1
                        if rl_attempt > MAX_RATELIMIT_RETRIES:
                            print(f"  Rate limit retries exhausted, skipping step", file=sys.stderr)
                            break
                        wait = min(15 * rl_attempt, 60)  # 15s, 30s, 45s, 60s cap
                        print(f"  Rate limited (rl attempt {rl_attempt}), waiting {wait}s...", file=sys.stderr)
                        # Ping the WebSocket every 5s during wait to prevent server-side close
                        slept = 0
                        while slept < wait:
                            await asyncio.sleep(min(5, wait - slept))
                            slept += 5
                            try:
                                pong = await ws.ping()
                                await asyncio.wait_for(pong, timeout=10)
                            except Exception:
                                pass  # connection issues handled by outer loop
                    else:
                        print(f"  LLM error (attempt {attempt + 1}): {e}", file=sys.stderr)
                        if attempt >= MAX_PARSE_RETRIES - 1 and rl_attempt == 0:
                            break  # non-429 errors stop after MAX_PARSE_RETRIES

            if action_dict is None:
                # Fallback: send an invalid action to let the env handle it
                action_dict = {"tool_name": "_invalid_", "parameters": {}}
                messages.append({"role": "assistant", "content": json.dumps(action_dict)})

            # Normalize "all" query param to empty string (handler uses it as substring filter)
            if action_dict.get("parameters", {}).get("query") == "all":
                action_dict["parameters"]["query"] = ""
            if action_dict.get("parameters", {}).get("severity") == "all":
                action_dict["parameters"].pop("severity", None)

            # Step the environment via WebSocket
            await ws.send(json.dumps({"type": "step", "data": action_dict}))
            resp = json.loads(await ws.recv())
            data = resp["data"]
            observation = data.get("observation", data)
            done = data.get("done", False)

            if observation.get("done"):
                done = True

            _raw_reward = data.get("reward")
            step_reward = float(_raw_reward) if _raw_reward is not None else 0.0
            cumulative_reward = observation.get("cumulative_reward", 0.0)
            rewards_list.append(f"{step_reward:.2f}")

            # Record trace for this step
            trace_steps.append({
                "step_number": step_num,
                "llm_call": {
                    "messages_sent": messages_snapshot,
                    "raw_output": raw,
                    "parse_attempts": parse_attempts,
                    "forced_resolution": force_resolution,
                    "latency_seconds": llm_latency,
                    "token_usage": token_usage,
                },
                "parsed_action": {
                    "tool_name": action_dict.get("tool_name"),
                    "parameters": action_dict.get("parameters", {}),
                },
                "env_response": {
                    "tool_output": observation.get("tool_output", ""),
                    "reward": step_reward,
                    "cumulative_reward": cumulative_reward,
                    "done": done,
                    "error": observation.get("last_action_error", ""),
                },
            })

            # [STEP] — mandatory structured log
            print(f"[STEP] step={step_num} action={action_dict.get('tool_name')} "
                  f"reward={step_reward:.2f} done={str(done).lower()} "
                  f"error={observation.get('last_action_error', 'null')}")

            # Add tool response as user message in the conversation
            if not done:
                messages.append({"role": "user", "content": build_tool_response_prompt(observation)})

        # Get final state for score
        await ws.send(json.dumps({"type": "state"}))
        resp = json.loads(await ws.recv())
        state_data = resp["data"]
        final_score = state_data.get("final_score", 1e-3)
        # Ensure score is strictly between 0 and 1
        _EPS = 1e-3
        final_score = max(_EPS, min(1.0 - _EPS, final_score))

        # [END] — mandatory structured log
        print(f"[END] success={str(final_score > 0).lower()} steps={local_step} "
              f"score={final_score:.2f} rewards={','.join(rewards_list)}")

        task_trace = {
            "task_id": task_id,
            "incident_summary": incident_summary,
            "final_score": final_score,
            "total_steps": local_step,
            "total_llm_calls": total_llm_calls,
            "steps": trace_steps,
        }
        return {"score": final_score, "trace": task_trace}


async def main() -> None:
    if USE_AZURE:
        llm_client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        global MODEL_NAME
        MODEL_NAME = AZURE_OPENAI_DEPLOYMENT
        print(f"Using Azure OpenAI: {AZURE_OPENAI_ENDPOINT} / deployment={MODEL_NAME}")
    elif USE_OPENROUTER:
        or_key = OPENROUTER_API_KEY or API_KEY
        or_headers = {"Authorization": f"Bearer {or_key}"}
        if OPENROUTER_SITE_URL:
            or_headers["HTTP-Referer"] = OPENROUTER_SITE_URL
        if OPENROUTER_SITE_NAME:
            or_headers["X-Title"] = OPENROUTER_SITE_NAME
        llm_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=or_key,
            default_headers=or_headers,
            http_client=httpx.Client(
                headers=or_headers,
                follow_redirects=True,
            ),
        )
        print(f"Using OpenRouter: https://openrouter.ai/api/v1 / model={MODEL_NAME}")
    else:
        llm_client = OpenAI(
            base_url=API_BASE_URL,
            api_key=API_KEY,
        )
        print(f"Using LLM API: {API_BASE_URL} / model={MODEL_NAME}")
    print(f"Environment URL: {ENV_URL}")

    scores: dict[int, float] = {}
    task_traces: list[dict] = []

    # Fix the trace filename at start so every incremental flush uses the same file
    run_start = datetime.now(timezone.utc)
    os.makedirs(TRACE_DIR, exist_ok=True)
    trace_basename = f"explainability_trace_{run_start.strftime('%Y%m%d_%H%M%S')}.json"
    trace_filename = os.path.join(TRACE_DIR, trace_basename)
    print(f"Trace file: {trace_filename}")

    def flush_trace() -> None:
        """Write the trace file with whatever tasks have completed so far."""
        avg_so_far = sum(scores.values()) / len(scores) if scores else 0.0
        trace_output = {
            "metadata": {
                "model_name": MODEL_NAME,
                "api_base_url": API_BASE_URL,
                "env_url": ENV_URL,
                "timestamp": run_start.isoformat(),
                "total_tasks": len(scores),
                "average_score": round(avg_so_far, 4),
                "status": "in_progress" if len(scores) < 3 else "complete",
            },
            "tasks": task_traces,
        }
        with open(trace_filename, "w") as f:
            json.dump(trace_output, f, indent=2, default=str)

    for task_id in [1, 2, 3]:
        print(f"\n{'='*50}")
        print(f"Running Task {task_id}...")
        print(f"{'='*50}")

        try:
            result = await asyncio.wait_for(
                run_task(task_id, ENV_URL, llm_client),
                timeout=TASK_TIMEOUT,
            )
            scores[task_id] = result["score"]
            task_traces.append(result["trace"])
        except asyncio.TimeoutError:
            print(f"  Task {task_id} timed out after {TASK_TIMEOUT}s", file=sys.stderr)
            scores[task_id] = 1e-3
            task_traces.append({
                "task_id": task_id, "incident_summary": "",
                "final_score": 1e-3, "total_steps": 0,
                "total_llm_calls": 0, "steps": [],
                "error": f"Timed out after {TASK_TIMEOUT}s",
            })
        except Exception as e:
            print(f"  Task {task_id} failed: {e}", file=sys.stderr)
            scores[task_id] = 1e-3
            task_traces.append({
                "task_id": task_id, "incident_summary": "",
                "final_score": 1e-3, "total_steps": 0,
                "total_llm_calls": 0, "steps": [],
                "error": str(e),
            })

        print(f"Task {task_id}: {scores[task_id]:.2f}")
        flush_trace()
        print(f"Trace updated: {trace_filename}")

    avg = sum(scores.values()) / len(scores) if scores else 0.0
    print(f"\n{'='*50}")
    print(f"Task 1: {scores.get(1, 0.0):.2f}")
    print(f"Task 2: {scores.get(2, 0.0):.2f}")
    print(f"Task 3: {scores.get(3, 0.0):.2f}")
    print(f"Average: {avg:.2f}")
    print(f"{'='*50}")
    print(f"\nExplainability trace written to: {trace_filename}")


if __name__ == "__main__":
    asyncio.run(main())
