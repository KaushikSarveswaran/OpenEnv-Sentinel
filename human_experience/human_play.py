"""Human-playable CLI for OpenEnv-Sentinel.

You ARE the agent. Investigate SRE incidents by calling tools,
then submit your verdict and get scored — just like the LLM agent.

Usage:
    python human_experience/human_play.py
    python human_experience/human_play.py --task 4
    python human_experience/human_play.py --url http://localhost:8000
"""

import argparse
import asyncio
import json
import sys
import textwrap
from typing import Optional

import websockets

# ── config ──────────────────────────────────────────────────────────

TASK_NAMES = {
    1: "The Smoking Gun",
    2: "The Upstream Culprit",
    3: "The Cascading Failure",
    4: "The DDoS Attack",
    5: "The Flash Sale Spike",
}

TOOL_HELP = {
    "get_service_status": {
        "desc": "Check health, error rate and latency of a service",
        "example": 'get_service_status api-gateway',
        "params": ["service"],
    },
    "query_logs": {
        "desc": "Fetch recent log lines for a service",
        "example": 'query_logs api-gateway',
        "params": ["service"],
    },
    "query_metrics": {
        "desc": "Pull a specific metric time-series for a service",
        "example": 'query_metrics api-gateway request_rate',
        "params": ["service", "metric"],
    },
    "get_dependency_map": {
        "desc": "Show service dependency graph (omit service for full map)",
        "example": 'get_dependency_map',
        "params": ["service (optional)"],
    },
    "consult_runbook": {
        "desc": "Look up an SRE runbook by topic",
        "example": 'consult_runbook high-error-rate',
        "params": ["topic"],
    },
    "check_recent_changes": {
        "desc": "List recent deployments and config changes",
        "example": 'check_recent_changes',
        "params": ["service (optional)"],
    },
    "submit_resolution": {
        "desc": "Submit your final verdict and get scored",
        "example": 'submit_resolution',
        "params": ["interactive prompts"],
    },
}

# ── ANSI colours ─────────────────────────────────────────────────────

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    CYAN    = "\033[36m"
    MAGENTA = "\033[35m"
    WHITE   = "\033[97m"
    DIM     = "\033[2m"
    BG_RED  = "\033[41m"
    BG_GREEN= "\033[42m"
    BG_BLUE = "\033[44m"

def bold(s):   return f"{C.BOLD}{s}{C.RESET}"
def red(s):    return f"{C.RED}{s}{C.RESET}"
def green(s):  return f"{C.GREEN}{s}{C.RESET}"
def yellow(s): return f"{C.YELLOW}{s}{C.RESET}"
def cyan(s):   return f"{C.CYAN}{s}{C.RESET}"
def magenta(s):return f"{C.MAGENTA}{s}{C.RESET}"
def dim(s):    return f"{C.DIM}{s}{C.RESET}"

# ── helpers ──────────────────────────────────────────────────────────

def divider(char="─", width=70, colour=C.DIM):
    print(f"{colour}{char * width}{C.RESET}")

def header(title: str):
    print()
    divider("═")
    print(f"{C.BOLD}{C.CYAN}  {title}{C.RESET}")
    divider("═")

def section(title: str):
    print()
    print(f"{C.BOLD}{C.YELLOW}▶ {title}{C.RESET}")
    divider()

def wrap(text: str, indent: int = 2) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=80, initial_indent=prefix, subsequent_indent=prefix)

def print_output(text: str):
    """Print tool output with subtle indentation."""
    print()
    for line in text.strip().splitlines():
        print(f"  {line}")
    print()

def score_bar(score: float, width: int = 30) -> str:
    filled = int(score * width)
    bar = "█" * filled + "░" * (width - filled)
    if score >= 0.8:
        colour = C.GREEN
    elif score >= 0.5:
        colour = C.YELLOW
    else:
        colour = C.RED
    return f"{colour}{bar}{C.RESET} {C.BOLD}{score:.2f}{C.RESET}"

# ── WebSocket helpers ────────────────────────────────────────────────

def _ws_url(base_url: str) -> str:
    return base_url.replace("http://", "ws://").replace("https://", "wss://").rstrip("/") + "/ws"

async def ws_reset(ws, task_id: int) -> dict:
    await ws.send(json.dumps({"type": "reset", "data": {"task_id": task_id}}))
    resp = json.loads(await ws.recv())
    data = resp["data"]
    return data.get("observation", data)

async def ws_step(ws, tool_name: str, params: dict) -> tuple[dict, bool]:
    await ws.send(json.dumps({"type": "step", "data": {"tool_name": tool_name, "parameters": params}}))
    resp = json.loads(await ws.recv())
    data = resp["data"]
    obs = data.get("observation", data)
    done = data.get("done", False) or obs.get("done", False)
    return obs, done

async def ws_get_state(ws) -> dict:
    await ws.send(json.dumps({"type": "state"}))
    resp = json.loads(await ws.recv())
    return resp["data"]

# ── tool call builders ───────────────────────────────────────────────

def build_params(tool_name: str, args: list[str]) -> Optional[dict]:
    """Convert positional CLI args into a params dict for a given tool."""
    if tool_name == "get_service_status":
        if not args:
            print(red("  ✗ Requires: get_service_status <service>"))
            return None
        return {"service": args[0]}

    elif tool_name == "query_logs":
        if not args:
            print(red("  ✗ Requires: query_logs <service>"))
            return None
        return {"service": args[0], "query": args[1] if len(args) > 1 else ""}

    elif tool_name == "query_metrics":
        if len(args) < 2:
            print(red("  ✗ Requires: query_metrics <service> <metric>"))
            print(dim("    Metrics: request_rate, error_rate, latency_p99, cpu, memory, connections, login_failure_rate, cache_hit_rate"))
            return None
        return {"service": args[0], "metric": args[1]}

    elif tool_name == "get_dependency_map":
        return {"service": args[0] if args else ""}

    elif tool_name == "consult_runbook":
        if not args:
            print(red("  ✗ Requires: consult_runbook <topic>"))
            return None
        return {"topic": " ".join(args)}

    elif tool_name == "check_recent_changes":
        return {"service": args[0] if args else ""}

    elif tool_name == "submit_resolution":
        return {}  # handled interactively

    return None

# ── submission wizard ────────────────────────────────────────────────

async def _ainput(prompt: str) -> str:
    """Non-blocking input() that keeps the asyncio event loop alive."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: input(prompt))

async def prompt_submission() -> Optional[dict]:
    section("SUBMIT RESOLUTION — Fill in your verdict")
    print(dim("  Press Ctrl+C to cancel and keep investigating.\n"))
    try:
        print(f"  {bold('Root cause')} (describe what caused the incident):")
        root_cause = (await _ainput("  > ")).strip()
        if not root_cause:
            print(red("  ✗ root_cause cannot be empty."))
            return None

        print(f"\n  {bold('Affected service')} (primary service impacted):")
        affected_service = (await _ainput("  > ")).strip()
        if not affected_service:
            print(red("  ✗ affected_service cannot be empty."))
            return None

        print(f"\n  {bold('Recommendation')} (what should be done to fix it):")
        recommendation = (await _ainput("  > ")).strip()
        if not recommendation:
            print(red("  ✗ recommendation cannot be empty."))
            return None

        print()
        print(bold("  Review your verdict:"))
        print(f"  {dim('Root cause:  ')}{root_cause}")
        print(f"  {dim('Service:     ')}{affected_service}")
        print(f"  {dim('Fix:         ')}{recommendation}")
        print()
        confirm = (await _ainput("  Submit? [y/N] > ")).strip().lower()
        if confirm != "y":
            print(dim("  Cancelled — keep investigating."))
            return None

        return {
            "root_cause": root_cause,
            "affected_service": affected_service,
            "recommendation": recommendation,
        }
    except KeyboardInterrupt:
        print(dim("\n  Cancelled."))
        return None

# ── results display ──────────────────────────────────────────────────

def show_results(obs: dict, step_count: int, final_score: float):
    score = final_score
    header("INVESTIGATION COMPLETE — YOUR RESULTS")

    print(f"\n  {bold('Final Score')}   {score_bar(score)}")
    print(f"  {bold('Steps used')}   {step_count}")
    print()

    # Score interpretation
    if score >= 0.9:
        verdict = green("★ Excellent — near-perfect diagnosis!")
    elif score >= 0.75:
        verdict = green("✓ Good — correct root cause identified")
    elif score >= 0.5:
        verdict = yellow("~ Partial — some key details missed")
    elif score >= 0.25:
        verdict = red("✗ Poor — wrong direction or missing specifics")
    else:
        verdict = red("✗ Missed — incorrect diagnosis")

    print(f"  {verdict}")
    print()

    # What the grader saw
    if obs.get("tool_output"):
        print(f"  {dim('Grader says:')} {obs['tool_output']}")
    print()
    divider("─")
    print(f"\n  {dim('Run again with:')} python human_experience/human_play.py\n")

# ── help display ─────────────────────────────────────────────────────

def show_help():
    print()
    print(bold("  Available commands:"))
    print()
    for name, info in TOOL_HELP.items():
        print(f"  {cyan(name)}")
        print(f"    {dim(info['desc'])}")
        print(f"    {dim('e.g.')} {info['example']}")
        print()
    print(f"  {cyan('help')}   — show this help")
    print(f"  {cyan('status')} — show step count and cumulative reward")
    print(f"  {cyan('quit')}   — exit without submitting")
    print()

# ── session status ───────────────────────────────────────────────────

def show_status(step_count: int, cumulative_reward: float, task_id: int, task_name: str):
    print()
    print(f"  {bold('Task')}              {task_id} — {task_name}")
    print(f"  {bold('Steps used')}       {step_count}  (max 20)")
    reward_str = green(f"{cumulative_reward:+.2f}") if cumulative_reward >= 0 else red(f"{cumulative_reward:+.2f}")
    print(f"  {bold('Cumulative reward')} {reward_str}")
    print()

# ── main game loop ────────────────────────────────────────────────────

async def play(base_url: str, task_id: int):
    ws_url = _ws_url(base_url)
    print(f"\n{dim('Connecting to')} {ws_url} ...")

    try:
        async with websockets.connect(ws_url, ping_interval=None) as ws:
            # ── Reset ───────────────────────────────────────────────────────
            try:
                obs = await ws_reset(ws, task_id)
            except Exception as e:
                print(red(f"\n  ✗ Reset failed: {e}"))
                sys.exit(1)

            task_name = TASK_NAMES.get(task_id, f"Task {task_id}")
            header(f"TASK {task_id}: {task_name.upper()}")

            # ── Incident brief ──────────────────────────────────────────────
            section("INCIDENT BRIEF")
            summary = obs.get("incident_summary", "")
            print_output(summary)

            # Tool descriptions (task-specific hints)
            tool_desc = obs.get("tool_descriptions", {})
            if tool_desc:
                print(f"  {bold('Available metrics & services for this task:')}")
                for k, v in tool_desc.items():
                    print(f"  {dim('•')} {cyan(k)}: {v}")
                print()

            divider()
            print(f"  {bold('Your job:')} Investigate the incident using the tools below,")
            print(f"  then {cyan('submit_resolution')} with your root cause and fix.")
            print(f"  Type {cyan('help')} for all commands.\n")

            step_count = 0
            cumulative_reward = 0.0

            # ── REPL ────────────────────────────────────────────────────────
            while True:
                try:
                    raw = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: input(f"{C.BOLD}{C.MAGENTA}sentinel{C.RESET} {dim(f'[step {step_count}]')} {C.BOLD}>{C.RESET} ").strip()
                    )
                except (KeyboardInterrupt, EOFError):
                    print(dim("\n\n  Use 'quit' to exit.\n"))
                    continue

                if not raw:
                    continue

                parts = raw.split()
                cmd = parts[0].lower()
                args = parts[1:]

                # ── meta commands ───────────────────────────────────────────
                if cmd in ("quit", "exit", "q"):
                    print(dim("\n  Exiting without submitting. Your score: ungraded.\n"))
                    return

                if cmd == "help":
                    show_help()
                    continue

                if cmd == "status":
                    show_status(step_count, cumulative_reward, task_id, task_name)
                    continue

                # ── tool commands ────────────────────────────────────────────
                if cmd not in TOOL_HELP:
                    print(red(f"  ✗ Unknown command '{cmd}'. Type 'help' to see all tools."))
                    continue

                # ── submit_resolution wizard ─────────────────────────────────
                if cmd == "submit_resolution":
                    params = await prompt_submission()
                    if params is None:
                        continue
                else:
                    params = build_params(cmd, args)
                    if params is None:
                        continue

                # ── send step to server ──────────────────────────────────────
                print(dim(f"  → {cmd}({json.dumps(params) if params else ''})"))

                try:
                    obs, done = await ws_step(ws, cmd, params)
                except Exception as e:
                    print(red(f"  ✗ WebSocket error: {e}"))
                    continue

                step_count += 1

                # Error from server
                err = obs.get("last_action_error", "")
                if err:
                    print(red(f"\n  ✗ {err}\n"))
                    step_count -= 1  # don't count invalid steps
                    continue

                # Reward tracking
                reward = obs.get("reward")
                if reward is not None:
                    cumulative_reward += reward

                # Done?
                if cmd == "submit_resolution" and done:
                    # Fetch final score from state
                    state = await ws_get_state(ws)
                    final_score = state.get("final_score", obs.get("reward", 0.0))
                    show_results(obs, step_count, final_score)
                    return

                # ── print tool output ────────────────────────────────────────
                output = obs.get("tool_output", "")
                if output:
                    section(f"RESULT: {cmd.upper()}")
                    print_output(output)
                else:
                    print(dim("  (no output)"))

                # Warn on too many steps
                if step_count >= 15:
                    print(yellow(f"\n  ⚠ Warning: {step_count}/20 steps used. Consider submitting soon.\n"))

    except (ConnectionRefusedError, OSError):
        print(red(f"\n  ✗ Cannot reach server at {base_url}"))
        print(dim(f"  Start it with: uv run python -m server.app"))
        sys.exit(1)

# ── entry point ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Play OpenEnv-Sentinel as a human agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Tasks:
              1 - The Smoking Gun       (easy)
              2 - The Upstream Culprit  (easy)
              3 - The Cascading Failure (hard)
              4 - The DDoS Attack       (medium)
              5 - The Flash Sale Spike  (medium)
        """),
    )
    parser.add_argument("--task", type=int, choices=[1, 2, 3, 4, 5], default=None,
                        help="Task ID to play (1-5). If omitted, you will be prompted.")
    parser.add_argument("--url", default="http://localhost:8000",
                        help="Sentinel server URL (default: http://localhost:8000)")
    args = parser.parse_args()

    # Task selection
    task_id = args.task
    if task_id is None:
        print()
        print(bold("  OpenEnv-Sentinel — Human Agent Mode"))
        print(dim("  You are the SRE. Investigate the incident and find the root cause.\n"))
        print("  Select a task:")
        for tid, name in TASK_NAMES.items():
            difficulty = {1: "easy", 2: "easy", 3: "hard", 4: "medium", 5: "medium"}[tid]
            diff_colour = green(difficulty) if difficulty == "easy" else (yellow(difficulty) if difficulty == "medium" else red(difficulty))
            print(f"    {bold(str(tid))}  {name}  {dim('(')} {diff_colour} {dim(')')}")
        print()
        while True:
            try:
                raw = input("  Enter task number [1-5]: ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                sys.exit(0)
            if raw.isdigit() and int(raw) in TASK_NAMES:
                task_id = int(raw)
                break
            print(red("  Invalid choice. Enter a number between 1 and 5."))

    asyncio.run(play(args.url, task_id))


if __name__ == "__main__":
    main()
