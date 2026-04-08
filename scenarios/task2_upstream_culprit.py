"""Task 2 — The Upstream Culprit: checkout latency caused by an upstream OOM."""

import re

from .base import BaseScenario


class UpstreamCulpritScenario(BaseScenario):
    """Checkout-service p99 latency caused by inventory-service OOMKilled restarts."""

    def __init__(self) -> None:
        self.incident_text = (
            "WARNING: checkout-service p99 latency > 5 seconds. "
            "Customer-facing degradation. SLA breach imminent."
        )

        self.services = {
            "checkout-service": {
                "name": "checkout-service",
                "status": "DEGRADED",
                "error_rate": "12%",
                "uptime": "99.7% (30d)",
                "last_deploy": "v3.8.0 deployed 2 days ago",
                "restarts": 0,
                "latency_p99": "5.2s",
                "connections": "38 active DB connections",
            },
            "inventory-service": {
                "name": "inventory-service",
                "status": "UNHEALTHY",
                "error_rate": "45%",
                "uptime": "94.2% (30d)",
                "last_deploy": "v2.1.4 deployed 5 days ago",
                "restarts": 4,
                "latency_p99": "timeout",
                "connections": "12 active DB connections",
            },
            "redis-cache": {
                "name": "redis-cache",
                "status": "HEALTHY",
                "error_rate": "0%",
                "uptime": "99.999% (30d)",
                "connections": "64 active connections",
            },
            "postgres-primary": {
                "name": "postgres-primary",
                "status": "HEALTHY",
                "error_rate": "0%",
                "uptime": "99.999% (30d)",
                "connections": "55 active connections",
            },
            "api-gateway": {
                "name": "api-gateway",
                "status": "HEALTHY",
                "error_rate": "2.1%",
                "uptime": "99.98% (30d)",
                "last_deploy": "v5.0.2 deployed 1 week ago",
                "latency_p99": "5.4s",
            },
        }

        self.log_entries = {
            "checkout-service": [
                {
                    "timestamp": "2026-04-01T09:31:04Z",
                    "level": "ERROR",
                    "message": "TimeoutException: inventory-service did not respond within 3000ms",
                    "source": "client.InventoryClient.checkStock(InventoryClient.java:67)",
                },
                {
                    "timestamp": "2026-04-01T09:31:18Z",
                    "level": "ERROR",
                    "message": "TimeoutException: inventory-service did not respond within 3000ms",
                    "source": "client.InventoryClient.checkStock(InventoryClient.java:67)",
                },
                {
                    "timestamp": "2026-04-01T09:31:22Z",
                    "level": "WARN",
                    "message": "Retry attempt 2/3 for inventory-service call failed",
                    "source": "client.InventoryClient.checkStock(InventoryClient.java:74)",
                },
                {
                    "timestamp": "2026-04-01T09:31:35Z",
                    "level": "ERROR",
                    "message": "TimeoutException: inventory-service did not respond within 3000ms",
                    "source": "client.InventoryClient.reserveItem(InventoryClient.java:112)",
                },
                {
                    "timestamp": "2026-04-01T09:31:48Z",
                    "level": "ERROR",
                    "message": "Failed to handle request POST /api/v1/checkout: HTTP 504 Gateway Timeout",
                    "source": "handler.CheckoutHandler.processCheckout(CheckoutHandler.java:91)",
                },
                {
                    "timestamp": "2026-04-01T09:32:01Z",
                    "level": "ERROR",
                    "message": "TimeoutException: inventory-service did not respond within 3000ms",
                    "source": "client.InventoryClient.checkStock(InventoryClient.java:67)",
                },
                {
                    "timestamp": "2026-04-01T09:32:15Z",
                    "level": "WARN",
                    "message": "Circuit breaker OPEN for inventory-service — too many failures",
                    "source": "circuitbreaker.CircuitBreakerManager.trip(CircuitBreakerManager.java:43)",
                },
                {
                    "timestamp": "2026-04-01T09:32:30Z",
                    "level": "INFO",
                    "message": "Circuit breaker HALF-OPEN for inventory-service — attempting probe",
                    "source": "circuitbreaker.CircuitBreakerManager.probe(CircuitBreakerManager.java:58)",
                },
                {
                    "timestamp": "2026-04-01T09:32:44Z",
                    "level": "ERROR",
                    "message": "TimeoutException: inventory-service did not respond within 3000ms",
                    "source": "client.InventoryClient.checkStock(InventoryClient.java:67)",
                },
                {
                    "timestamp": "2026-04-01T09:32:58Z",
                    "level": "WARN",
                    "message": "Circuit breaker OPEN for inventory-service — probe failed",
                    "source": "circuitbreaker.CircuitBreakerManager.trip(CircuitBreakerManager.java:43)",
                },
            ],
            "inventory-service": [
                {
                    "timestamp": "2026-04-01T09:15:02Z",
                    "level": "INFO",
                    "message": "Starting catalog sync batch job — processing 12,400 items",
                    "source": "jobs.CatalogSyncJob.execute(CatalogSyncJob.java:38)",
                },
                {
                    "timestamp": "2026-04-01T09:18:33Z",
                    "level": "WARN",
                    "message": "GC overhead limit exceeded — 98% of time spent in GC",
                    "source": "runtime.GarbageCollector",
                },
                {
                    "timestamp": "2026-04-01T09:19:47Z",
                    "level": "ERROR",
                    "message": "java.lang.OutOfMemoryError: Java heap space",
                    "source": "jobs.CatalogSyncJob.processBatch(CatalogSyncJob.java:85)",
                },
                {
                    "timestamp": "2026-04-01T09:19:48Z",
                    "level": "ERROR",
                    "message": "OOMKilled: Container exceeded memory limit 512Mi",
                    "source": "kubernetes.ContainerRuntime",
                },
                {
                    "timestamp": "2026-04-01T09:19:50Z",
                    "level": "INFO",
                    "message": "Container restarting (restart count: 1)",
                    "source": "kubernetes.ContainerRuntime",
                },
                {
                    "timestamp": "2026-04-01T09:20:15Z",
                    "level": "INFO",
                    "message": "Application started: inventory-service v2.1.4",
                    "source": "main.Application.start(Application.java:15)",
                },
                {
                    "timestamp": "2026-04-01T09:20:18Z",
                    "level": "INFO",
                    "message": "Resuming catalog sync batch job — 8,200 items remaining",
                    "source": "jobs.CatalogSyncJob.execute(CatalogSyncJob.java:42)",
                },
                {
                    "timestamp": "2026-04-01T09:24:11Z",
                    "level": "WARN",
                    "message": "GC overhead limit exceeded — 97% of time spent in GC",
                    "source": "runtime.GarbageCollector",
                },
                {
                    "timestamp": "2026-04-01T09:25:03Z",
                    "level": "ERROR",
                    "message": "java.lang.OutOfMemoryError: Java heap space",
                    "source": "jobs.CatalogSyncJob.processBatch(CatalogSyncJob.java:85)",
                },
                {
                    "timestamp": "2026-04-01T09:25:04Z",
                    "level": "ERROR",
                    "message": "OOMKilled: Container exceeded memory limit 512Mi",
                    "source": "kubernetes.ContainerRuntime",
                },
                {
                    "timestamp": "2026-04-01T09:25:06Z",
                    "level": "INFO",
                    "message": "Container restarting (restart count: 2)",
                    "source": "kubernetes.ContainerRuntime",
                },
                {
                    "timestamp": "2026-04-01T09:25:30Z",
                    "level": "INFO",
                    "message": "Application started: inventory-service v2.1.4",
                    "source": "main.Application.start(Application.java:15)",
                },
                {
                    "timestamp": "2026-04-01T09:29:41Z",
                    "level": "ERROR",
                    "message": "java.lang.OutOfMemoryError: Java heap space",
                    "source": "jobs.CatalogSyncJob.processBatch(CatalogSyncJob.java:85)",
                },
                {
                    "timestamp": "2026-04-01T09:29:42Z",
                    "level": "ERROR",
                    "message": "OOMKilled: Container exceeded memory limit 512Mi",
                    "source": "kubernetes.ContainerRuntime",
                },
                {
                    "timestamp": "2026-04-01T09:29:44Z",
                    "level": "INFO",
                    "message": "Container restarting (restart count: 3)",
                    "source": "kubernetes.ContainerRuntime",
                },
                {
                    "timestamp": "2026-04-01T09:30:10Z",
                    "level": "INFO",
                    "message": "Application started: inventory-service v2.1.4",
                    "source": "main.Application.start(Application.java:15)",
                },
                {
                    "timestamp": "2026-04-01T09:33:58Z",
                    "level": "ERROR",
                    "message": "java.lang.OutOfMemoryError: Java heap space",
                    "source": "jobs.CatalogSyncJob.processBatch(CatalogSyncJob.java:85)",
                },
                {
                    "timestamp": "2026-04-01T09:33:59Z",
                    "level": "ERROR",
                    "message": "OOMKilled: Container exceeded memory limit 512Mi",
                    "source": "kubernetes.ContainerRuntime",
                },
                {
                    "timestamp": "2026-04-01T09:34:01Z",
                    "level": "INFO",
                    "message": "Container restarting (restart count: 4)",
                    "source": "kubernetes.ContainerRuntime",
                },
            ],
        }

        self.metrics = {
            "inventory-service": {
                "memory": {
                    "values": [
                        ("2026-04-01T09:15:00Z", "210Mi"),
                        ("2026-04-01T09:16:00Z", "280Mi"),
                        ("2026-04-01T09:17:00Z", "380Mi"),
                        ("2026-04-01T09:18:00Z", "450Mi"),
                        ("2026-04-01T09:19:00Z", "510Mi"),
                        ("2026-04-01T09:19:47Z", "OOMKilled"),
                        ("2026-04-01T09:20:15Z", "120Mi"),
                        ("2026-04-01T09:22:00Z", "260Mi"),
                        ("2026-04-01T09:24:00Z", "440Mi"),
                        ("2026-04-01T09:25:00Z", "510Mi"),
                        ("2026-04-01T09:25:03Z", "OOMKilled"),
                        ("2026-04-01T09:25:30Z", "125Mi"),
                        ("2026-04-01T09:28:00Z", "390Mi"),
                        ("2026-04-01T09:29:41Z", "OOMKilled"),
                        ("2026-04-01T09:30:10Z", "118Mi"),
                        ("2026-04-01T09:33:00Z", "480Mi"),
                        ("2026-04-01T09:33:58Z", "OOMKilled"),
                    ],
                    "unit": "mebibytes",
                    "annotation": "RSS climbing: 380Mi → 450Mi → 510Mi → OOMKilled → restart → climb again. Memory limit: 512Mi.",
                },
                "cpu": {
                    "values": [
                        ("2026-04-01T09:15:00Z", "15%"),
                        ("2026-04-01T09:16:00Z", "32%"),
                        ("2026-04-01T09:17:00Z", "58%"),
                        ("2026-04-01T09:18:00Z", "74%"),
                        ("2026-04-01T09:19:00Z", "91%"),
                        ("2026-04-01T09:19:47Z", "99%"),
                        ("2026-04-01T09:20:15Z", "8%"),
                        ("2026-04-01T09:22:00Z", "35%"),
                        ("2026-04-01T09:24:00Z", "72%"),
                        ("2026-04-01T09:25:03Z", "98%"),
                        ("2026-04-01T09:25:30Z", "10%"),
                        ("2026-04-01T09:29:41Z", "97%"),
                        ("2026-04-01T09:30:10Z", "9%"),
                        ("2026-04-01T09:33:58Z", "96%"),
                    ],
                    "unit": "percent",
                    "annotation": "CPU spikes correlated with OOM events — GC thrashing before each kill.",
                },
            },
            "checkout-service": {
                "latency_p99": {
                    "values": [
                        ("2026-04-01T09:10:00Z", "180ms"),
                        ("2026-04-01T09:15:00Z", "190ms"),
                        ("2026-04-01T09:19:00Z", "3200ms"),
                        ("2026-04-01T09:20:00Z", "5100ms"),
                        ("2026-04-01T09:22:00Z", "1400ms"),
                        ("2026-04-01T09:25:00Z", "5200ms"),
                        ("2026-04-01T09:27:00Z", "2100ms"),
                        ("2026-04-01T09:29:00Z", "4800ms"),
                        ("2026-04-01T09:31:00Z", "5200ms"),
                        ("2026-04-01T09:33:00Z", "5400ms"),
                    ],
                    "unit": "milliseconds",
                    "annotation": "Latency spikes correlate with inventory-service restart cycles.",
                },
                "error_rate": {
                    "values": [
                        ("2026-04-01T09:10:00Z", "0.3%"),
                        ("2026-04-01T09:15:00Z", "0.4%"),
                        ("2026-04-01T09:19:00Z", "8.2%"),
                        ("2026-04-01T09:20:00Z", "14.1%"),
                        ("2026-04-01T09:22:00Z", "5.3%"),
                        ("2026-04-01T09:25:00Z", "15.0%"),
                        ("2026-04-01T09:27:00Z", "6.1%"),
                        ("2026-04-01T09:29:00Z", "11.8%"),
                        ("2026-04-01T09:31:00Z", "12.0%"),
                        ("2026-04-01T09:33:00Z", "13.5%"),
                    ],
                    "unit": "percent",
                    "annotation": "Timeout errors from inventory-service dependency.",
                },
            },
        }

        self.dependency_map = {
            "api-gateway": {
                "depends_on": ["checkout-service"],
                "depended_by": [],
            },
            "checkout-service": {
                "depends_on": ["inventory-service", "redis-cache"],
                "depended_by": ["api-gateway"],
            },
            "inventory-service": {
                "depends_on": ["redis-cache", "postgres-primary"],
                "depended_by": ["checkout-service"],
            },
            "redis-cache": {
                "depends_on": [],
                "depended_by": ["checkout-service", "inventory-service"],
            },
            "postgres-primary": {
                "depends_on": [],
                "depended_by": ["inventory-service"],
            },
        }

        self.recent_changes = {
            "checkout-service": [
                {
                    "timestamp": "2026-03-30T11:00:00Z",
                    "service": "checkout-service",
                    "description": "Deployed v3.8.0",
                    "changelog": "Added coupon validation at checkout. Minor UI fixes.",
                },
            ],
            "inventory-service": [
                {
                    "timestamp": "2026-03-27T16:30:00Z",
                    "service": "inventory-service",
                    "description": "Deployed v2.1.4",
                    "changelog": "Bumped catalog sync batch size from 500 to 5000 items per batch for throughput improvement.",
                },
                {
                    "timestamp": "2026-04-01T09:14:00Z",
                    "service": "inventory-service",
                    "description": "Scheduled catalog sync job triggered",
                    "changelog": "Cron job started full catalog sync — 12,400 items to process.",
                },
            ],
            "api-gateway": [
                {
                    "timestamp": "2026-03-25T09:00:00Z",
                    "service": "api-gateway",
                    "description": "Deployed v5.0.2",
                    "changelog": "Updated rate limiting configuration.",
                },
            ],
        }

        self.runbooks = {
            "inventory-service": (
                "## Runbook: inventory-service\n\n"
                "### Common Issues\n\n"
                "1. **OOMKilled / Memory Issues**\n"
                "   - Check current memory usage: `kubectl top pod -l app=inventory-service`\n"
                "   - Review Java heap settings: `-Xmx` should be ~75% of container memory limit.\n"
                "   - If caused by batch processing, reduce batch size or increase memory limit.\n"
                "   - Current memory limit: 512Mi. Recommended: 1Gi for large catalog syncs.\n"
                "   - To increase limit: `kubectl set resources deployment/inventory-service --limits=memory=1Gi`\n\n"
                "2. **High Latency / Timeouts**\n"
                "   - Check downstream dependencies (redis-cache, postgres-primary).\n"
                "   - Verify connection pool is not exhausted.\n"
                "   - If service is in restart loop, check for OOMKilled events.\n\n"
                "### Scaling\n"
                "   ```\n"
                "   kubectl scale deployment/inventory-service --replicas=3\n"
                "   ```\n\n"
                "### Escalation\n"
                "   Contact: #inventory-oncall in Slack\n"
            ),
            "checkout-service": (
                "## Runbook: checkout-service\n\n"
                "### Common Issues\n\n"
                "1. **High Latency**\n"
                "   - Check upstream dependencies: inventory-service, redis-cache.\n"
                "   - Verify circuit breaker state.\n"
                "   - If inventory-service is down, checkout will degrade.\n\n"
                "2. **Timeout Errors**\n"
                "   - Default timeout to inventory-service: 3000ms.\n"
                "   - If inventory-service is restarting frequently, consider enabling graceful degradation mode.\n\n"
                "### Escalation\n"
                "   Contact: #checkout-oncall in Slack\n"
            ),
            "oom troubleshooting": (
                "## Runbook: OOM Troubleshooting (General)\n\n"
                "### Symptoms\n"
                "- Container status: OOMKilled\n"
                "- Repeated restarts in `kubectl get pods`\n"
                "- Java services: `java.lang.OutOfMemoryError: Java heap space`\n\n"
                "### Investigation Steps\n"
                "1. Check container memory limit vs actual usage: `kubectl top pod`\n"
                "2. Review JVM heap settings: `-Xmx`, `-Xms`\n"
                "3. Look for memory leak patterns: steady RSS climb → OOM → restart → climb\n"
                "4. Check for recent changes that increased memory footprint (batch sizes, cache sizes).\n\n"
                "### Immediate Mitigation\n"
                "- Increase memory limit: `kubectl set resources deployment/<name> --limits=memory=<new_limit>`\n"
                "- Reduce workload (e.g. smaller batch sizes).\n"
                "- Restart with profiling enabled to capture heap dump: `-XX:+HeapDumpOnOutOfMemoryError`\n\n"
                "### Long-term Fix\n"
                "- Profile heap usage and fix leak.\n"
                "- Use streaming/pagination instead of loading full batches into memory.\n"
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
            "get_service_status:checkout-service",
            "query_logs:checkout-service",
            "get_dependency_map:checkout-service",
            "get_service_status:inventory-service",
            "query_logs:inventory-service",
            "query_metrics:inventory-service:memory",
        ]

    def get_tool_descriptions(self) -> dict:
        return {
            "query_logs": {
                "services": list(self.services.keys()),
                "severity_options": ["all", "error", "warning", "info"],
            },
            "query_metrics": {
                "services": list(self.metrics.keys()),
                "metrics": ["cpu", "memory", "error_rate", "latency", "connections"],
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

        # Root cause identifies OOM/memory in inventory-service (0.30)
        memory_keywords = ["memory", "oom", "outofmemory", "outofmemoryerror", "oomkilled"]
        has_memory = any(kw in root_cause_text for kw in memory_keywords)
        has_inventory = "inventory" in root_cause_text
        root_cause_memory = has_memory and has_inventory
        if root_cause_memory:
            score += 0.30

        # Identifies checkout latency caused by inventory (0.15)
        upstream_keywords = ["upstream", "dependency"]
        inventory_checkout_keywords_a = ["inventory"]
        inventory_checkout_keywords_b = ["checkout", "timeout", "latency"]
        upstream_match = any(kw in root_cause_text for kw in upstream_keywords)
        inv_checkout_match = (
            any(kw in root_cause_text for kw in inventory_checkout_keywords_a)
            and any(kw in root_cause_text for kw in inventory_checkout_keywords_b)
        )
        if upstream_match or inv_checkout_match:
            score += 0.15

        # Affected service is inventory-service (0.15)
        affected_normalized = re.sub(r"[^a-z0-9-]", "", affected)
        if affected_normalized == "inventory-service":
            score += 0.15
        # Score 0.0 if they say checkout-service (no partial credit)

        # Recommendation addresses memory (0.20)
        rec_keywords = [
            "memory limit", "heap", "batch", "stream", "1gi",
            "increase memory", "reduce batch", "xmx",
        ]
        rec_match = any(kw in recommendation_text for kw in rec_keywords)
        if rec_match:
            score += 0.20

        # Efficiency bonus (0.10)
        if step_count <= 8:
            score += 0.10
        elif step_count <= 12:
            score += 0.05

        # No destructive recommendations (0.10) — present by default
        destructive_keywords = ["restart-all", "drop", "delete"]
        destructive = any(kw in recommendation_text for kw in destructive_keywords)
        if not destructive:
            score += 0.10

        root_cause_correct = root_cause_memory
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
