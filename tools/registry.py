"""Tool registry — validates and dispatches tool calls to the active scenario."""

from typing import Tuple

from scenarios.base import BaseScenario

AVAILABLE_TOOLS = [
    "query_logs",
    "query_metrics",
    "get_service_status",
    "get_dependency_map",
    "consult_runbook",
    "check_recent_changes",
    "submit_resolution",
]


def make_relevance_key(tool_name: str, params: dict) -> str:
    """Build a colon-joined relevance key from tool name and significant params.

    Examples:
        make_relevance_key("query_logs", {"service": "auth"}) -> "query_logs:auth"
        make_relevance_key("get_dependency_map", {}) -> "get_dependency_map"
    """
    parts = [tool_name]
    for k in ("service", "metric", "topic"):
        v = params.get(k)
        if v:
            parts.append(str(v))
    return ":".join(parts)


def dispatch(tool_name: str, params: dict, scenario: BaseScenario) -> Tuple[str, bool]:
    """Dispatch a tool call to the scenario.

    Returns (output_text, is_valid).
    is_valid=False means the tool_name was unknown or parameters were malformed.
    """
    if tool_name not in AVAILABLE_TOOLS:
        return (
            f"Unknown tool '{tool_name}'. Available tools: {', '.join(AVAILABLE_TOOLS)}",
            False,
        )

    if tool_name == "submit_resolution":
        # submit_resolution is handled by the environment directly, not here
        return ("", True)

    return (scenario.get_tool_response(tool_name, params), True)
