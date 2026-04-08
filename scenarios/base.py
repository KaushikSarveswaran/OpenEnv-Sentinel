"""Base scenario ABC for SRE incident triage tasks."""

from abc import ABC, abstractmethod
from typing import Dict, List


class BaseScenario(ABC):
    """Abstract base for all incident scenarios."""

    @abstractmethod
    def get_incident_summary(self) -> str:
        """Return the initial alert text for this incident."""

    @abstractmethod
    def get_services(self) -> Dict[str, dict]:
        """Return service status data."""

    @abstractmethod
    def get_tool_response(self, tool_name: str, parameters: dict) -> str:
        """Return a pre-scripted response for the given tool call."""

    @abstractmethod
    def get_relevant_tools(self) -> List[str]:
        """Return list of 'tool_name:param' string keys considered relevant."""

    @abstractmethod
    def grade_resolution(self, resolution: dict, step_count: int) -> dict:
        """Grade a submitted resolution. Returns dict with score, root_cause_correct, recommendation_correct."""

    @abstractmethod
    def get_tool_descriptions(self) -> dict:
        """Return parameter metadata for LLM context. Called once on reset."""

    # ── shared helpers ──────────────────────────────────────────────

    def _format_logs(self, entries: List[dict]) -> str:
        lines = []
        for e in entries:
            lines.append(f"[{e['timestamp']}] {e['level']} - {e['message']}")
            if "source" in e:
                lines.append(f"    at {e['source']}")
        return "\n".join(lines) if lines else "No matching log entries found."

    def _format_metrics(self, metric_name: str, data: dict) -> str:
        lines = [f"Metric: {metric_name}"]
        if "values" in data:
            lines.append(f"  Values (recent): {data['values']}")
        if "unit" in data:
            lines.append(f"  Unit: {data['unit']}")
        if "annotation" in data:
            lines.append(f"  ⚠ {data['annotation']}")
        return "\n".join(lines)

    def _format_service_status(self, svc: dict) -> str:
        lines = [
            f"Service: {svc['name']}",
            f"  Status: {svc['status']}",
            f"  Error Rate: {svc.get('error_rate', 'N/A')}",
            f"  Uptime: {svc.get('uptime', 'N/A')}",
        ]
        if "last_deploy" in svc:
            lines.append(f"  Last Deploy: {svc['last_deploy']}")
        if "restarts" in svc:
            lines.append(f"  Restarts (30min): {svc['restarts']}")
        if "latency_p99" in svc:
            lines.append(f"  Latency (p99): {svc['latency_p99']}")
        if "queue_depth" in svc:
            lines.append(f"  Queue Depth: {svc['queue_depth']}")
        if "connections" in svc:
            lines.append(f"  Connections: {svc['connections']}")
        return "\n".join(lines)

    def _format_dependency_map(self, deps: dict) -> str:
        lines = []
        for svc, info in deps.items():
            depends_on = ", ".join(info.get("depends_on", []))
            depended_by = ", ".join(info.get("depended_by", []))
            lines.append(f"{svc}:")
            if depends_on:
                lines.append(f"  Depends on: {depends_on}")
            if depended_by:
                lines.append(f"  Depended on by: {depended_by}")
        return "\n".join(lines) if lines else "No dependency data available."

    def _format_changes(self, changes: List[dict]) -> str:
        if not changes:
            return "No recent changes found."
        lines = []
        for c in changes:
            lines.append(f"[{c['timestamp']}] {c['service']} - {c['description']}")
            if "changelog" in c:
                lines.append(f"  Changelog: {c['changelog']}")
        return "\n".join(lines)

    def _format_runbook(self, content: str) -> str:
        return content if content else "No matching runbook found for this topic."
