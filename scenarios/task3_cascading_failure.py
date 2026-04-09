"""Task 3 — The Cascading Failure: analytics-worker long query exhausts postgres pool."""

import re
from typing import Dict, List

from .base import BaseScenario


class CascadingFailureScenario(BaseScenario):
    """Multiple services degraded due to postgres connection pool exhaustion caused by analytics-worker."""

    def __init__(self) -> None:
        self.incident_text = (
            "CRITICAL: Multiple services degraded. auth-service, user-profile-service, "
            "notification-service all reporting errors. PagerDuty escalation triggered."
        )

        self.services: Dict[str, dict] = {
            "auth-service": {
                "name": "auth-service",
                "status": "UNHEALTHY",
                "error_rate": "98%",
                "uptime": "87.2% (24h)",
                "last_deploy": "v5.2.0 deployed 2 days ago",
                "latency_p99": "timeout",
            },
            "user-profile-service": {
                "name": "user-profile-service",
                "status": "UNHEALTHY",
                "error_rate": "85%",
                "uptime": "91.0% (24h)",
                "last_deploy": "v2.4.1 deployed 1 week ago",
                "latency_p99": "timeout",
            },
            "notification-service": {
                "name": "notification-service",
                "status": "DEGRADED",
                "error_rate": "45%",
                "uptime": "94.5% (24h)",
                "last_deploy": "v3.1.0 deployed 30 minutes ago",
                "queue_depth": "15420 (normal < 100)",
            },
            "postgres-primary": {
                "name": "postgres-primary",
                "status": "DEGRADED",
                "error_rate": "0%",
                "uptime": "99.999% (30d)",
                "connections": "50/50 active (pool exhausted), 23 waiting",
            },
            "analytics-worker": {
                "name": "analytics-worker",
                "status": "HEALTHY",
                "error_rate": "0%",
                "uptime": "99.9% (30d)",
                "last_deploy": "v1.9.0 deployed 1 week ago",
            },
            "api-gateway": {
                "name": "api-gateway",
                "status": "DEGRADED",
                "error_rate": "62%",
                "uptime": "93.1% (24h)",
                "last_deploy": "v8.0.3 deployed 3 days ago",
                "latency_p99": "12.4s",
            },
        }

        self.log_entries: Dict[str, List[dict]] = {
            "auth-service": [
                {
                    "timestamp": "2026-04-01T14:32:10Z",
                    "level": "ERROR",
                    "message": "PSQLException: Cannot acquire connection from pool. Pool exhausted (max=50, active=50, idle=0)",
                    "source": "com.auth.db.ConnectionManager.getConnection()",
                },
                {
                    "timestamp": "2026-04-01T14:32:12Z",
                    "level": "ERROR",
                    "message": "PSQLException: Cannot acquire connection from pool. Pool exhausted (max=50, active=50, idle=0)",
                    "source": "com.auth.db.ConnectionManager.getConnection()",
                },
                {
                    "timestamp": "2026-04-01T14:32:14Z",
                    "level": "ERROR",
                    "message": "Failed to validate authentication token: database connection unavailable",
                    "source": "com.auth.service.TokenValidator.validate()",
                },
                {
                    "timestamp": "2026-04-01T14:32:16Z",
                    "level": "WARN",
                    "message": "Health check failing: cannot reach database",
                    "source": "com.auth.health.DatabaseHealthCheck",
                },
                {
                    "timestamp": "2026-04-01T14:32:18Z",
                    "level": "ERROR",
                    "message": "PSQLException: Cannot acquire connection from pool. Pool exhausted (max=50, active=50, idle=0)",
                    "source": "com.auth.db.ConnectionManager.getConnection()",
                },
            ],
            "user-profile-service": [
                {
                    "timestamp": "2026-04-01T14:32:11Z",
                    "level": "ERROR",
                    "message": "AuthenticationException: Token validation failed - auth-service unreachable",
                    "source": "com.userprofile.auth.AuthClient.validateToken()",
                },
                {
                    "timestamp": "2026-04-01T14:32:13Z",
                    "level": "ERROR",
                    "message": "HTTP 401 Unauthorized: auth-service returned connection timeout",
                    "source": "com.userprofile.auth.AuthClient.validateToken()",
                },
                {
                    "timestamp": "2026-04-01T14:32:15Z",
                    "level": "WARN",
                    "message": "Falling back to cached user profile for user_id=8821 (auth unavailable)",
                    "source": "com.userprofile.service.ProfileService.getProfile()",
                },
                {
                    "timestamp": "2026-04-01T14:32:17Z",
                    "level": "ERROR",
                    "message": "AuthenticationException: Token validation failed - auth-service unreachable",
                    "source": "com.userprofile.auth.AuthClient.validateToken()",
                },
            ],
            "notification-service": [
                {
                    "timestamp": "2026-04-01T14:32:12Z",
                    "level": "ERROR",
                    "message": "UserProfileException: Cannot fetch user preferences - user-profile-service returned 401",
                    "source": "com.notification.client.UserProfileClient.getPreferences()",
                },
                {
                    "timestamp": "2026-04-01T14:32:14Z",
                    "level": "WARN",
                    "message": "Notification queue depth: 15420 (threshold: 1000). Processing stalled.",
                    "source": "com.notification.queue.QueueMonitor",
                },
                {
                    "timestamp": "2026-04-01T14:32:16Z",
                    "level": "ERROR",
                    "message": "UserProfileException: Cannot fetch user preferences - user-profile-service returned 401",
                    "source": "com.notification.client.UserProfileClient.getPreferences()",
                },
                {
                    "timestamp": "2026-04-01T14:32:18Z",
                    "level": "INFO",
                    "message": "v3.1.0 deployment completed successfully. New feature: batch notification grouping.",
                    "source": "com.notification.deploy.DeploymentHook",
                },
            ],
            "postgres-primary": [
                {
                    "timestamp": "2026-04-01T14:10:05Z",
                    "level": "LOG",
                    "message": "duration: 1245032.456 ms  statement: SELECT e.event_id, e.event_type, e.created_at, u.user_name, u.email, s.session_data FROM events e JOIN users u ON e.user_id = u.id JOIN sessions s ON e.session_id = s.id WHERE e.created_at > '2026-01-01' AND e.event_type IN ('purchase', 'refund', 'chargeback') ORDER BY e.created_at  -- analytics_worker scheduled_report",
                    "source": "postgres/slow_query_log",
                },
                {
                    "timestamp": "2026-04-01T14:25:30Z",
                    "level": "WARN",
                    "message": "connection pool near capacity: 48/50 active connections",
                    "source": "postgres/connection_monitor",
                },
                {
                    "timestamp": "2026-04-01T14:28:00Z",
                    "level": "ERROR",
                    "message": "connection pool exhausted: 50/50 active connections, 12 clients waiting",
                    "source": "postgres/connection_monitor",
                },
                {
                    "timestamp": "2026-04-01T14:30:15Z",
                    "level": "ERROR",
                    "message": "connection pool exhausted: 50/50 active connections, 23 clients waiting. Longest query running for 1221s (analytics_worker)",
                    "source": "postgres/connection_monitor",
                },
            ],
            "analytics-worker": [
                {
                    "timestamp": "2026-04-01T14:10:00Z",
                    "level": "INFO",
                    "message": "Starting scheduled report: quarterly_event_analysis. Estimated rows: 4.2M",
                    "source": "com.analytics.scheduler.ReportRunner",
                },
                {
                    "timestamp": "2026-04-01T14:10:05Z",
                    "level": "INFO",
                    "message": "Executing query against postgres-primary (no read replica configured)",
                    "source": "com.analytics.db.QueryExecutor",
                },
                {
                    "timestamp": "2026-04-01T14:32:00Z",
                    "level": "INFO",
                    "message": "Query still running. Rows processed so far: 2.1M of estimated 4.2M",
                    "source": "com.analytics.scheduler.ReportRunner",
                },
            ],
            "api-gateway": [
                {
                    "timestamp": "2026-04-01T14:32:10Z",
                    "level": "ERROR",
                    "message": "Upstream timeout: auth-service did not respond within 5000ms",
                    "source": "com.gateway.proxy.UpstreamHandler",
                },
                {
                    "timestamp": "2026-04-01T14:32:12Z",
                    "level": "ERROR",
                    "message": "Upstream timeout: user-profile-service did not respond within 5000ms",
                    "source": "com.gateway.proxy.UpstreamHandler",
                },
                {
                    "timestamp": "2026-04-01T14:32:15Z",
                    "level": "WARN",
                    "message": "Circuit breaker OPEN for auth-service (failure rate: 98%)",
                    "source": "com.gateway.circuit.CircuitBreaker",
                },
            ],
        }

        self.metrics: Dict[str, Dict[str, dict]] = {
            "postgres-primary": {
                "connections": {
                    "values": [42, 44, 46, 48, 49, 50, 50, 50, 50, 50],
                    "unit": "active connections (max 50)",
                    "annotation": "Connection pool saturated at 14:28. 48 connections held by analytics_worker query. 23 queries waiting.",
                },
                "cpu": {
                    "values": [15, 18, 22, 35, 42, 55, 58, 60, 62, 61],
                    "unit": "percent",
                    "annotation": "CPU elevated due to long-running analytics query (full table scan + joins).",
                },
            },
            "analytics-worker": {
                "cpu": {
                    "values": [5, 5, 8, 12, 15, 15, 14, 15, 14, 15],
                    "unit": "percent",
                    "annotation": "Stable elevated CPU — analytics query in progress since 14:10.",
                },
                "memory": {
                    "values": [210, 215, 220, 225, 230, 235, 240, 245, 248, 250],
                    "unit": "Mi",
                    "annotation": "Memory slowly climbing as query result set grows. Within limits (512Mi).",
                },
            },
            "auth-service": {
                "error_rate": {
                    "values": [0.1, 0.1, 0.2, 5.0, 45.0, 88.0, 95.0, 97.0, 98.0, 98.0],
                    "unit": "percent",
                    "annotation": "Error rate spike correlates with postgres pool exhaustion at 14:28.",
                },
                "latency": {
                    "values": [50, 55, 120, 800, 3000, 5000, 5000, 5000, 5000, 5000],
                    "unit": "ms (p99)",
                    "annotation": "Latency spike to timeout threshold. Auth requests waiting for DB connections.",
                },
            },
            "notification-service": {
                "queue_depth": {
                    "values": [45, 50, 80, 350, 1200, 4500, 8200, 11000, 13800, 15420],
                    "unit": "messages",
                    "annotation": "Queue backlog growing rapidly. Processing stalled due to user-profile-service failures.",
                },
            },
        }

        self.dependency_map: Dict[str, dict] = {
            "api-gateway": {
                "depends_on": ["auth-service", "user-profile-service", "notification-service"],
                "depended_by": [],
            },
            "auth-service": {
                "depends_on": ["postgres-primary"],
                "depended_by": ["api-gateway", "user-profile-service"],
            },
            "user-profile-service": {
                "depends_on": ["auth-service"],
                "depended_by": ["api-gateway", "notification-service"],
            },
            "notification-service": {
                "depends_on": ["user-profile-service"],
                "depended_by": ["api-gateway"],
            },
            "postgres-primary": {
                "depends_on": [],
                "depended_by": ["auth-service", "analytics-worker"],
            },
            "analytics-worker": {
                "depends_on": ["postgres-primary"],
                "depended_by": [],
            },
        }

        self.recent_changes: Dict[str, List[dict]] = {
            "notification-service": [
                {
                    "timestamp": "2026-04-01T14:02:00Z",
                    "service": "notification-service",
                    "description": "Deployed v3.1.0 — batch notification grouping feature",
                    "changelog": "Added batch grouping for push notifications. No database schema changes.",
                },
            ],
            "analytics-worker": [
                {
                    "timestamp": "2026-04-01T14:10:00Z",
                    "service": "analytics-worker",
                    "description": "Scheduled job started: quarterly_event_analysis",
                    "changelog": "Automated quarterly report. Runs against postgres-primary (no read replica configured).",
                },
            ],
            "": [  # all recent changes
                {
                    "timestamp": "2026-04-01T14:02:00Z",
                    "service": "notification-service",
                    "description": "Deployed v3.1.0 — batch notification grouping feature",
                    "changelog": "Added batch grouping for push notifications. No database schema changes.",
                },
                {
                    "timestamp": "2026-04-01T14:10:00Z",
                    "service": "analytics-worker",
                    "description": "Scheduled job started: quarterly_event_analysis",
                    "changelog": "Automated quarterly report. Runs against postgres-primary (no read replica configured).",
                },
            ],
        }

        self.runbooks: Dict[str, str] = {
            "connection pool exhausted": (
                "Runbook: PostgreSQL Connection Pool Exhausted\n"
                "1. Check active connections: SELECT count(*) FROM pg_stat_activity;\n"
                "2. Identify long-running queries: SELECT pid, now()-query_start AS duration, query FROM pg_stat_activity WHERE state='active' ORDER BY duration DESC;\n"
                "3. Kill the offending query: SELECT pg_terminate_backend(<pid>);\n"
                "4. Monitor pool recovery — connections should free up within seconds.\n"
                "5. Prevent recurrence: Set statement_timeout for batch jobs. Consider using a read replica for analytics."
            ),
            "connection pool": (
                "Runbook: PostgreSQL Connection Pool Exhausted\n"
                "1. Check active connections: SELECT count(*) FROM pg_stat_activity;\n"
                "2. Identify long-running queries: SELECT pid, now()-query_start AS duration, query FROM pg_stat_activity WHERE state='active' ORDER BY duration DESC;\n"
                "3. Kill the offending query: SELECT pg_terminate_backend(<pid>);\n"
                "4. Monitor pool recovery — connections should free up within seconds.\n"
                "5. Prevent recurrence: Set statement_timeout for batch jobs. Consider using a read replica for analytics."
            ),
            "authentication failure": (
                "Runbook: Authentication Service Failures\n"
                "1. Check auth-service health: GET /health\n"
                "2. Verify database connectivity from auth-service.\n"
                "3. Check for recent auth-service deployments.\n"
                "4. If DB connection issue, check postgres connection pool status.\n"
                "5. Escalate to DBA if postgres is the bottleneck."
            ),
            "notification queue": (
                "Runbook: Notification Queue Backlog\n"
                "1. Check queue depth and processing rate.\n"
                "2. Verify upstream dependencies (user-profile-service).\n"
                "3. Check for recent notification-service deployments.\n"
                "4. If upstream is down, queue will naturally drain once restored.\n"
                "5. Do NOT restart notification-service — this will lose queued messages."
            ),
        }

    # ── public interface ────────────────────────────────────────────

    def get_incident_summary(self) -> str:
        return self.incident_text

    def get_services(self) -> Dict[str, dict]:
        return self.services

    def get_tool_response(self, tool_name: str, parameters: dict) -> str:
        handlers = {
            "get_service_status": self._handle_service_status,
            "query_logs": self._handle_query_logs,
            "query_metrics": self._handle_query_metrics,
            "get_dependency_map": self._handle_dependency_map,
            "consult_runbook": self._handle_runbook,
            "check_recent_changes": self._handle_recent_changes,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            return f"Tool '{tool_name}' is not available."
        return handler(parameters)

    def get_relevant_tools(self) -> list[str]:
        return [
            "get_service_status:auth-service",
            "query_logs:auth-service",
            "get_service_status:postgres-primary",
            "query_metrics:postgres-primary:connections",
            "query_logs:postgres-primary",
            "get_dependency_map",
            "consult_runbook:connection pool",
            "get_service_status:analytics-worker",
            "query_metrics:analytics-worker",
            "check_recent_changes",
        ]

    def get_tool_descriptions(self) -> dict:
        return {
            "query_logs": {
                "services": list(self.services.keys()),
                "severity_options": ["all", "error", "warning", "info"],
            },
            "query_metrics": {
                "services": list(self.metrics.keys()),
                "metrics": ["connections", "cpu", "memory", "error_rate", "latency", "queue_depth"],
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
        root_cause = resolution.get("root_cause", "").lower()
        affected = resolution.get("affected_service", "").lower().strip().replace("_", "-")
        recommendation = resolution.get("recommendation", "").lower()

        score = 0.0

        # Root cause identifies postgres connection pool exhaustion (0.20)
        pool_terms = any(t in root_cause for t in ["connection pool", "connections"])
        exhausted_terms = any(t in root_cause for t in ["exhausted", "maxed", "full", "saturated"])
        pool_match = pool_terms and exhausted_terms
        if pool_match:
            score += 0.20

        # Root cause identifies analytics-worker / long-running query (0.20)
        analytics_match_a = "analytics" in root_cause
        analytics_match_b = any(t in root_cause for t in ["query", "long-running", "holding connections", "long query"])
        analytics_match = analytics_match_a and analytics_match_b
        if analytics_match:
            score += 0.20

        # Understands cascade chain (0.10)
        cascade_kw = "cascade" in root_cause
        # Or mentions 3+ services in the chain
        chain_services = ["auth", "user-profile", "notification", "postgres"]
        chain_count = sum(1 for s in chain_services if s in root_cause)
        if cascade_kw or chain_count >= 3:
            score += 0.10

        # Affected service is postgres-primary or analytics-worker (0.10)
        valid_affected = {"postgres-primary", "postgres", "analytics-worker", "analytics"}
        bad_affected = {"auth-service", "notification-service", "user-profile-service"}
        if affected in valid_affected:
            score += 0.10
        elif affected in bad_affected:
            score += 0.0  # explicit 0

        # Does NOT blame notification-service deploy (0.05) — present by default
        notif_blamed = ("notification" in root_cause) and any(
            t in root_cause for t in ["deploy", "v3.1"]
        )
        if not notif_blamed:
            score += 0.05

        # Recommendation: kill query + prevent recurrence (0.15)
        kill_match = any(t in recommendation for t in ["kill", "terminate"]) and "query" in recommendation
        prevent_match = any(
            t in recommendation
            for t in ["timeout", "read replica", "pgbouncer", "statement_timeout", "pool"]
        )
        if kill_match and prevent_match:
            score += 0.15
        elif kill_match or prevent_match:
            score += 0.07

        # Efficiency bonus (0.10)
        if step_count <= 12:
            score += 0.10
        elif step_count <= 16:
            score += 0.05

        # No destructive recommendations (0.10) — present by default
        has_kill_query = bool(re.search(r"kill.*query|terminate.*query", recommendation))
        destructive_terms = ["restart postgres", "drop connections", "restart-all"]
        is_destructive = any(t in recommendation for t in destructive_terms) and not has_kill_query
        if not is_destructive:
            score += 0.10

        root_cause_correct = pool_match and analytics_match
        recommendation_correct = kill_match and prevent_match

        _EPS = 1e-3
        score = max(_EPS, min(1.0 - _EPS, score))
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
            return f"Service '{service}' not found in this environment."
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
        if not matched:
            return f"No matching log entries found for '{service}' with query '{query}'."
        return self._format_logs(matched)

    def _handle_query_metrics(self, parameters: dict) -> str:
        service = parameters.get("service", "")
        metric = parameters.get("metric", "").lower()
        svc_metrics = self.metrics.get(service)
        if svc_metrics is None:
            return f"No metrics available for service '{service}'."
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
        topic = parameters.get("topic", "").lower()
        for key, value in self.runbooks.items():
            if topic and topic in key.lower():
                return self._format_runbook(value)
        return self._format_runbook("")

    def _handle_recent_changes(self, parameters: dict) -> str:
        service = parameters.get("service", "")
        if service and service in self.recent_changes:
            return self._format_changes(self.recent_changes[service])
        # No service specified — return all
        return self._format_changes(self.recent_changes.get("", []))
