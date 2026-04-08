"""Task 1 — The Smoking Gun: a clear-cut deployment-caused outage."""

import re

from .base import BaseScenario


class SmokingGunScenario(BaseScenario):
    """Payment-API HTTP 500s caused by a missing env var after deploy v2.3.1."""

    def __init__(self) -> None:
        self.incident_text = (
            "CRITICAL: payment-api returning HTTP 500 errors. "
            "Customer checkout failing. Started 10 minutes ago."
        )

        self.services = {
            "payment-api": {
                "name": "payment-api",
                "status": "UNHEALTHY",
                "error_rate": "92%",
                "uptime": "99.3% (30d)",
                "last_deploy": "v2.3.1 deployed 8 minutes ago",
                "restarts": 0,
                "latency_p99": "timeout",
                "connections": "0 active DB connections",
            },
            "order-service": {
                "name": "order-service",
                "status": "HEALTHY",
                "error_rate": "0.1%",
                "uptime": "99.99% (30d)",
                "last_deploy": "v4.1.0 deployed 3 days ago",
                "latency_p99": "120ms",
            },
            "user-service": {
                "name": "user-service",
                "status": "HEALTHY",
                "error_rate": "0.05%",
                "uptime": "99.99% (30d)",
                "last_deploy": "v1.8.2 deployed 5 days ago",
                "latency_p99": "45ms",
            },
            "postgres-primary": {
                "name": "postgres-primary",
                "status": "HEALTHY",
                "error_rate": "0%",
                "uptime": "99.999% (30d)",
                "connections": "42 active connections",
            },
        }

        self.log_entries = {
            "payment-api": [
                {
                    "timestamp": "2026-04-01T10:32:14Z",
                    "level": "ERROR",
                    "message": "NullPointerException: DB_CONNECTION_STRING is null",
                    "source": "config.DatabaseConfig.getConnection(DatabaseConfig.java:42)",
                },
                {
                    "timestamp": "2026-04-01T10:32:16Z",
                    "level": "ERROR",
                    "message": "NullPointerException: DB_CONNECTION_STRING is null",
                    "source": "config.DatabaseConfig.getConnection(DatabaseConfig.java:42)",
                },
                {
                    "timestamp": "2026-04-01T10:32:18Z",
                    "level": "ERROR",
                    "message": "NullPointerException: DB_CONNECTION_STRING is null",
                    "source": "config.DatabaseConfig.getConnection(DatabaseConfig.java:42)",
                },
                {
                    "timestamp": "2026-04-01T10:32:20Z",
                    "level": "ERROR",
                    "message": "Failed to handle request POST /api/v1/payments: HTTP 500",
                    "source": "handler.PaymentHandler.processPayment(PaymentHandler.java:87)",
                },
                {
                    "timestamp": "2026-04-01T10:32:22Z",
                    "level": "ERROR",
                    "message": "NullPointerException: DB_CONNECTION_STRING is null",
                    "source": "config.DatabaseConfig.getConnection(DatabaseConfig.java:42)",
                },
                {
                    "timestamp": "2026-04-01T10:32:24Z",
                    "level": "WARN",
                    "message": "Health check failed: unable to reach database",
                    "source": "health.HealthCheckService.check(HealthCheckService.java:23)",
                },
                {
                    "timestamp": "2026-04-01T10:32:26Z",
                    "level": "ERROR",
                    "message": "NullPointerException: DB_CONNECTION_STRING is null",
                    "source": "config.DatabaseConfig.getConnection(DatabaseConfig.java:42)",
                },
                {
                    "timestamp": "2026-04-01T10:32:28Z",
                    "level": "ERROR",
                    "message": "Failed to handle request POST /api/v1/payments: HTTP 500",
                    "source": "handler.PaymentHandler.processPayment(PaymentHandler.java:87)",
                },
                {
                    "timestamp": "2026-04-01T10:32:30Z",
                    "level": "INFO",
                    "message": "Application started: payment-api v2.3.1",
                    "source": "main.Application.start(Application.java:15)",
                },
                {
                    "timestamp": "2026-04-01T10:32:32Z",
                    "level": "ERROR",
                    "message": "NullPointerException: DB_CONNECTION_STRING is null",
                    "source": "config.DatabaseConfig.getConnection(DatabaseConfig.java:42)",
                },
            ],
        }

        self.metrics = {
            "payment-api": {
                "error_rate": {
                    "values": [
                        ("2026-04-01T10:20:00Z", "0.1%"),
                        ("2026-04-01T10:22:00Z", "0.1%"),
                        ("2026-04-01T10:24:00Z", "0.1%"),
                        ("2026-04-01T10:25:00Z", "92.0%"),
                        ("2026-04-01T10:26:00Z", "92.3%"),
                        ("2026-04-01T10:28:00Z", "91.8%"),
                        ("2026-04-01T10:30:00Z", "92.1%"),
                        ("2026-04-01T10:32:00Z", "92.0%"),
                    ],
                    "unit": "percent",
                    "annotation": "Spike at 10:25:00Z correlates with deploy v2.3.1",
                },
                "latency_p99": {
                    "values": [
                        ("2026-04-01T10:20:00Z", "85ms"),
                        ("2026-04-01T10:22:00Z", "82ms"),
                        ("2026-04-01T10:24:00Z", "88ms"),
                        ("2026-04-01T10:25:00Z", "timeout"),
                        ("2026-04-01T10:26:00Z", "timeout"),
                        ("2026-04-01T10:28:00Z", "timeout"),
                        ("2026-04-01T10:30:00Z", "timeout"),
                        ("2026-04-01T10:32:00Z", "timeout"),
                    ],
                    "unit": "milliseconds",
                    "annotation": "Latency spiked to timeout at deploy timestamp",
                },
                "request_count": {
                    "values": [
                        ("2026-04-01T10:20:00Z", "1200"),
                        ("2026-04-01T10:22:00Z", "1180"),
                        ("2026-04-01T10:24:00Z", "1210"),
                        ("2026-04-01T10:25:00Z", "1195"),
                        ("2026-04-01T10:26:00Z", "1050"),
                        ("2026-04-01T10:28:00Z", "870"),
                        ("2026-04-01T10:30:00Z", "620"),
                        ("2026-04-01T10:32:00Z", "430"),
                    ],
                    "unit": "requests/min",
                    "annotation": "Request volume dropping as clients receive errors",
                },
            },
        }

        self.dependency_map = {
            "payment-api": {
                "depends_on": ["postgres-primary", "user-service"],
                "depended_by": ["order-service"],
            },
            "order-service": {
                "depends_on": ["payment-api", "postgres-primary"],
                "depended_by": [],
            },
            "user-service": {
                "depends_on": ["postgres-primary"],
                "depended_by": ["payment-api"],
            },
            "postgres-primary": {
                "depends_on": [],
                "depended_by": ["payment-api", "order-service", "user-service"],
            },
        }

        self.recent_changes = {
            "payment-api": [
                {
                    "timestamp": "2026-04-01T10:24:30Z",
                    "service": "payment-api",
                    "description": "Deployed v2.3.1",
                    "changelog": "Refactored config loader to use new ConfigManager class. Removed legacy environment variable fallback.",
                },
            ],
            "order-service": [
                {
                    "timestamp": "2026-03-29T14:00:00Z",
                    "service": "order-service",
                    "description": "Deployed v4.1.0",
                    "changelog": "Added bulk order endpoint.",
                },
            ],
        }

        self.runbooks = {
            "payment-api": (
                "## Runbook: payment-api\n\n"
                "### Common Issues\n\n"
                "1. **HTTP 500 errors**\n"
                "   - Check database connectivity: verify DB_CONNECTION_STRING env var is set.\n"
                "   - Check connection pool exhaustion: review active connections on postgres-primary.\n"
                "   - If caused by a bad deploy, rollback to previous version.\n\n"
                "2. **High latency**\n"
                "   - Check postgres-primary slow query log.\n"
                "   - Review connection pool settings.\n\n"
                "### Rollback Procedure\n"
                "   ```\n"
                "   kubectl rollout undo deployment/payment-api\n"
                "   ```\n\n"
                "### Escalation\n"
                "   Contact: #payments-oncall in Slack\n"
            ),
        }

    # ── abstract method implementations ─────────────────────────────

    def get_incident_summary(self) -> str:
        return self.incident_text

    def get_services(self) -> dict:
        return self.services

    def get_tool_response(self, tool_name: str, parameters: dict) -> str:
        dispatch = {
            "get_service_status": self._handle_service_status,
            "query_logs": self._handle_query_logs,
            "query_metrics": self._handle_query_metrics,
            "get_dependency_map": self._handle_dependency_map,
            "consult_runbook": self._handle_runbook,
            "check_recent_changes": self._handle_recent_changes,
        }
        handler = dispatch.get(tool_name)
        if handler is None:
            return f"Unknown tool: {tool_name}"
        return handler(parameters)

    def get_relevant_tools(self) -> list[str]:
        return [
            "get_service_status:payment-api",
            "query_logs:payment-api",
            "check_recent_changes:payment-api",
            "query_metrics:payment-api:error_rate",
        ]

    def get_tool_descriptions(self) -> dict:
        return {
            "query_logs": {
                "services": list(self.services.keys()),
                "severity_options": ["all", "error", "warning", "info"],
            },
            "query_metrics": {
                "services": list(self.metrics.keys()),
                "metrics": ["error_rate", "latency_p99", "request_count", "cpu", "memory"],
            },
            "get_service_status": {
                "services": list(self.services.keys()),
            },
            "get_dependency_map": {
                "services": list(self.dependency_map.keys()),
                "note": "Omit service for full map",
            },
            "consult_runbook": {
                "topics": list(self.runbooks.keys()),
            },
            "check_recent_changes": {
                "services": list(self.recent_changes.keys()),
                "note": "Omit service for all changes",
            },
        }

    def grade_resolution(self, resolution: dict, step_count: int) -> dict:
        score = 0.0
        root_cause_text = str(resolution.get("root_cause", "")).lower()
        affected = str(resolution.get("affected_service", "")).strip().lower()
        recommendation_text = str(resolution.get("recommendation", "")).lower()

        # Root cause mentions config/env var issue (0.30)
        config_match = False
        if "db_connection_string" in root_cause_text:
            config_match = True
        elif any(kw in root_cause_text for kw in ["environment variable", "env var", "config"]):
            if any(kw in root_cause_text for kw in ["missing", "null", "empty"]):
                config_match = True
        if config_match:
            score += 0.30

        # Root cause mentions deployment (0.20)
        deploy_match = any(
            kw in root_cause_text for kw in ["deploy", "v2.3.1", "release", "v2.3"]
        )
        if deploy_match:
            score += 0.20

        # Affected service is payment-api (0.15)
        if affected == "payment-api":
            score += 0.15

        # Recommendation includes rollback or fix (0.15)
        rec_match = False
        if any(kw in recommendation_text for kw in ["rollback", "revert"]):
            rec_match = True
        elif re.search(r"set.*db_connection", recommendation_text):
            rec_match = True
        elif re.search(r"configure.*db_connection", recommendation_text):
            rec_match = True
        if rec_match:
            score += 0.15

        # Efficiency bonus (0.10)
        if step_count <= 5:
            score += 0.10
        elif step_count <= 8:
            score += 0.05

        # No destructive recommendations (0.10) — present by default
        destructive = any(
            kw in recommendation_text
            for kw in ["restart-all", "drop database", "delete", "truncate"]
        )
        if not destructive:
            score += 0.10

        root_cause_correct = config_match and deploy_match
        recommendation_correct = rec_match

        score = max(0.0, min(1.0, score))
        return {
            "score": score,
            "root_cause_correct": root_cause_correct,
            "recommendation_correct": recommendation_correct,
        }

    # ── internal tool handlers ──────────────────────────────────────

    def _handle_service_status(self, parameters: dict) -> str:
        service = parameters.get("service", "")
        svc = self.services.get(service)
        if svc is None:
            return f"Service '{service}' not found."
        return self._format_service_status(svc)

    def _handle_query_logs(self, parameters: dict) -> str:
        service = parameters.get("service", "")
        query = parameters.get("query", "").lower()
        entries = self.log_entries.get(service)
        if entries is None:
            return f"No logs available for service '{service}'."
        if query:
            matched = [
                e
                for e in entries
                if query in e["message"].lower()
                or query in e.get("level", "").lower()
                or query in e.get("source", "").lower()
            ]
        else:
            matched = entries
        return self._format_logs(matched)

    def _handle_query_metrics(self, parameters: dict) -> str:
        service = parameters.get("service", "")
        metric = parameters.get("metric", "").lower()
        svc_metrics = self.metrics.get(service)
        if svc_metrics is None:
            return f"No metrics available for service '{service}'."
        # Fuzzy substring match on metric name
        for name, data in svc_metrics.items():
            if metric in name.lower() or name.lower() in metric:
                return self._format_metrics(name, data)
        return f"No matching metric '{metric}' for service '{service}'."

    def _handle_dependency_map(self, parameters: dict) -> str:
        service = parameters.get("service", "")
        if service and service in self.dependency_map:
            subset = {service: self.dependency_map[service]}
            return self._format_dependency_map(subset)
        return self._format_dependency_map(self.dependency_map)

    def _handle_runbook(self, parameters: dict) -> str:
        service = parameters.get("service", "")
        topic = parameters.get("topic", "").lower()
        # Try service-specific runbook first
        content = self.runbooks.get(service)
        if content:
            return self._format_runbook(content)
        # Try topic match
        for key, value in self.runbooks.items():
            if topic and topic in key.lower():
                return self._format_runbook(value)
        return self._format_runbook("")

    def _handle_recent_changes(self, parameters: dict) -> str:
        service = parameters.get("service", "")
        changes = self.recent_changes.get(service)
        if changes is None:
            return f"No recent changes found for service '{service}'."
        return self._format_changes(changes)
