"""Task 5 — The Flash Sale Spike: api-gateway rate-limiting due to legitimate traffic surge."""

import re

from .base import BaseScenario


class FlashSaleSpikeScenario(BaseScenario):
    """api-gateway 429s caused by a legitimate traffic surge from a marketing campaign.
    Rate limit config was never updated to account for the expected load increase."""

    def __init__(self) -> None:
        self.incident_text = (
            "CRITICAL: api-gateway rejection rate spiked from 10% to 54%. "
            "Customers reporting inability to complete purchases. HTTP 429 Too Many Requests. "
            "Started 9 minutes ago."
        )

        self.services = {
            "api-gateway": {
                "name": "api-gateway",
                "status": "DEGRADED",
                "error_rate": "54%",
                "uptime": "99.8% (30d)",
                "last_deploy": "v5.2.0 deployed 3 days ago",
                "restarts": 0,
                "latency_p99": "22ms",
                "connections": "15,200 active (normal: ~1,200)",
            },
            "product-service": {
                "name": "product-service",
                "status": "DEGRADED",
                "error_rate": "18%",
                "uptime": "99.6% (30d)",
                "last_deploy": "v4.3.2 deployed 5 days ago",
                "restarts": 0,
                "latency_p99": "620ms",
                "connections": "N/A",
            },
            "order-service": {
                "name": "order-service",
                "status": "HEALTHY",
                "error_rate": "1.1%",
                "uptime": "99.99% (30d)",
                "last_deploy": "v6.0.1 deployed 7 days ago",
                "latency_p99": "130ms",
            },
            "redis-cache": {
                "name": "redis-cache",
                "status": "HEALTHY",
                "error_rate": "0%",
                "uptime": "99.999% (30d)",
                "connections": "88 active connections",
            },
            "marketing-campaign-service": {
                "name": "marketing-campaign-service",
                "status": "HEALTHY",
                "error_rate": "0%",
                "uptime": "99.9% (30d)",
                "last_deploy": "v1.4.0 deployed 32 minutes ago",
            },
        }

        self.log_entries = {
            "api-gateway": [
                # Realistic Envoy access log entries — diverse IPs, real browser UAs, mixed endpoints
                {
                    "timestamp": "2026-04-12T09:01:12.043Z",
                    "level": "INFO",
                    "message": '203.0.113.44 "GET /api/products?sale=true&category=electronics HTTP/1.1" 200 rt=88ms ua="Mozilla/5.0 (iPhone; CPU iPhone OS 17_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"',
                    "source": "envoy.access_log",
                },
                {
                    "timestamp": "2026-04-12T09:01:12.091Z",
                    "level": "INFO",
                    "message": '198.51.100.82 "GET /api/products?sale=true&category=clothing HTTP/1.1" 200 rt=92ms ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"',
                    "source": "envoy.access_log",
                },
                {
                    "timestamp": "2026-04-12T09:01:12.204Z",
                    "level": "INFO",
                    "message": '192.0.2.17 "POST /api/checkout HTTP/1.1" 200 rt=142ms ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"',
                    "source": "envoy.access_log",
                },
                {
                    "timestamp": "2026-04-12T09:02:00.001Z",
                    "level": "WARN",
                    "message": "Global rate limit approaching: 14,200/15,000 req/min. Traffic ramp ongoing.",
                    "source": "ratelimiter.GlobalLimiter.check(GlobalLimiter.java:34)",
                },
                {
                    "timestamp": "2026-04-12T09:02:30.114Z",
                    "level": "INFO",
                    "message": (
                        "60s traffic window: 14,850 requests from 9,420 unique IPs across 42 distinct endpoints. "
                        "Top endpoints: GET /api/products?sale=true (44%), POST /api/checkout (26%), "
                        "GET /api/cart (17%), GET /api/products?sale=true&category=electronics (8%), other (5%). "
                        "Max per-IP rate: 12 req/s (user 203.0.113.44). Median: 1.3 req/s."
                    ),
                    "source": "metrics.TrafficAnalyzer.periodicReport(TrafficAnalyzer.java:89)",
                },
                {
                    "timestamp": "2026-04-12T09:03:00.002Z",
                    "level": "ERROR",
                    "message": "Global rate limit exceeded: 15,100/15,000 req/min. Returning HTTP 429 to new requests.",
                    "source": "ratelimiter.GlobalLimiter.check(GlobalLimiter.java:38)",
                },
                {
                    "timestamp": "2026-04-12T09:03:15.330Z",
                    "level": "INFO",
                    "message": (
                        "User-agent breakdown (last 5min): "
                        "Chrome desktop 34%, Safari mobile 28%, Chrome mobile 21%, Firefox 9%, "
                        "Samsung Internet 5%, other browsers 3%. Zero bot signatures detected."
                    ),
                    "source": "metrics.UserAgentAnalyzer.log(UserAgentAnalyzer.java:42)",
                },
                {
                    "timestamp": "2026-04-12T09:03:30.441Z",
                    "level": "INFO",
                    "message": (
                        "Geographic distribution: US-East 31%, US-West 21%, Europe 24%, APAC 18%, Other 6%. "
                        "Request spike pattern consistent with push notification delivery wave (mobile-heavy, geographically distributed)."
                    ),
                    "source": "metrics.GeoAnalyzer.log(GeoAnalyzer.java:30)",
                },
                {
                    "timestamp": "2026-04-12T09:04:00.005Z",
                    "level": "WARN",
                    "message": "429 rejection rate 54.1%: 8,154 of 15,100 requests dropped. No single IP rate exceeds 14 req/s. All dropped requests are legitimate browser sessions.",
                    "source": "ratelimiter.RateLimiter.enforce(RateLimiter.java:104)",
                },
                {
                    "timestamp": "2026-04-12T09:04:30.009Z",
                    "level": "INFO",
                    "message": "Active rate limit config: GLOBAL_RATE_LIMIT=15000 req/min, PER_IP_RATE_LIMIT=100 req/s. Config last modified: 2026-04-09T11:00:00Z.",
                    "source": "config.RateLimitConfig.dump(RateLimitConfig.java:20)",
                },
                {
                    "timestamp": "2026-04-12T09:05:00.002Z",
                    "level": "WARN",
                    "message": "Upstream product-service p99 latency 620ms (SLA: 200ms). Downstream errors causing compounding 429s on retried requests.",
                    "source": "proxy.UpstreamProxy.route(UpstreamProxy.java:77)",
                },
            ],
            "product-service": [
                {
                    "timestamp": "2026-04-12T09:00:10Z",
                    "level": "WARN",
                    "message": "HikariCP connection pool: 38/40 connections active. Avg wait time 185ms (warn threshold: 100ms).",
                    "source": "com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:213)",
                },
                {
                    "timestamp": "2026-04-12T09:01:00Z",
                    "level": "WARN",
                    "message": "Redis cache miss rate elevated: 71% (baseline: 11%). Cause: new query params (?sale=true, ?sale=true&category=*) not present in warm cache keys.",
                    "source": "cache.ProductCacheManager.get(ProductCacheManager.java:88)",
                },
                {
                    "timestamp": "2026-04-12T09:02:00Z",
                    "level": "ERROR",
                    "message": "HikariCP: Connection is not available, request timed out after 30001ms. Pool: 40/40 active, 0 idle, 142 threads waiting.",
                    "source": "com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:227)",
                },
                {
                    "timestamp": "2026-04-12T09:02:15Z",
                    "level": "ERROR",
                    "message": "Returning HTTP 503 Service Unavailable: DB connection pool exhausted. Not a code error — service saturated by request volume.",
                    "source": "handler.ProductHandler.respond(ProductHandler.java:91)",
                },
                {
                    "timestamp": "2026-04-12T09:03:00Z",
                    "level": "WARN",
                    "message": "Thread pool utilisation 97% (194/200 threads). Executor queue depth: 1,840 pending requests.",
                    "source": "server.ThreadPoolMonitor.report(ThreadPoolMonitor.java:55)",
                },
                {
                    "timestamp": "2026-04-12T09:04:00Z",
                    "level": "INFO",
                    "message": "Slow query log: SELECT * FROM products WHERE sale=true ORDER BY discount_pct DESC — avg 310ms (baseline: 18ms). Table scan due to missing index on (sale, discount_pct).",
                    "source": "db.SlowQueryLogger.log(SlowQueryLogger.java:44)",
                },
            ],
            "marketing-campaign-service": [
                {
                    "timestamp": "2026-04-12T08:55:00Z",
                    "level": "INFO",
                    "message": "Pre-flight check passed. Campaign 'spring-flash-sale-2026' ready for activation. Audience: 2.1M push subscribers, 800K email list.",
                    "source": "campaign.PreflightChecker.run(PreflightChecker.java:40)",
                },
                {
                    "timestamp": "2026-04-12T08:58:00Z",
                    "level": "INFO",
                    "message": "Campaign v1.4.0 activated. Push notifications dispatched to 2,143,820 devices. Email send job enqueued for 812,400 addresses. Estimated interaction rate: 4-7% within first 15 minutes.",
                    "source": "campaign.CampaignController.activate(CampaignController.java:33)",
                },
                {
                    "timestamp": "2026-04-12T08:58:32Z",
                    "level": "INFO",
                    "message": "Push delivery confirmed: 1,988,104 delivered, 155,716 failed (device offline). Deep-link target: /api/products?sale=true",
                    "source": "campaign.PushDeliveryTracker.report(PushDeliveryTracker.java:61)",
                },
                {
                    "timestamp": "2026-04-12T09:01:44Z",
                    "level": "INFO",
                    "message": "Campaign click-through rate: 6.2% (124,062 taps in first 3 min). Conversion funnel: product-view → cart → checkout.",
                    "source": "campaign.AnalyticsCollector.report(AnalyticsCollector.java:78)",
                },
            ],
        }

        self.metrics = {
            "api-gateway": {
                "request_rate": {
                    "values": [
                        ("2026-04-12T08:53:00Z", "1,152 req/min"),
                        ("2026-04-12T08:54:00Z", "1,168 req/min"),
                        ("2026-04-12T08:55:00Z", "1,181 req/min"),
                        ("2026-04-12T08:56:00Z", "1,159 req/min"),
                        ("2026-04-12T08:57:00Z", "1,163 req/min"),
                        ("2026-04-12T08:58:00Z", "2,104 req/min"),   # campaign push delivery starts
                        ("2026-04-12T08:59:00Z", "5,390 req/min"),
                        ("2026-04-12T09:00:00Z", "9,820 req/min"),
                        ("2026-04-12T09:01:00Z", "13,180 req/min"),
                        ("2026-04-12T09:02:00Z", "14,850 req/min"),
                        ("2026-04-12T09:03:00Z", "15,100 req/min"),
                        ("2026-04-12T09:04:00Z", "15,210 req/min"),
                        ("2026-04-12T09:05:00Z", "15,190 req/min"),
                    ],
                    "unit": "requests/min",
                    "annotation": "Smooth ramp over ~5min beginning 08:58Z. Shape matches a push notification wave — devices open app progressively as notifications arrive.",
                },
                "error_rate": {
                    "values": [
                        ("2026-04-12T08:53:00Z", "0.9%"),
                        ("2026-04-12T08:57:00Z", "0.9%"),
                        ("2026-04-12T08:58:00Z", "1.1%"),
                        ("2026-04-12T08:59:00Z", "8.4%"),
                        ("2026-04-12T09:00:00Z", "24.3%"),
                        ("2026-04-12T09:01:00Z", "41.8%"),
                        ("2026-04-12T09:02:00Z", "51.9%"),
                        ("2026-04-12T09:03:00Z", "54.1%"),
                        ("2026-04-12T09:04:00Z", "54.3%"),
                        ("2026-04-12T09:05:00Z", "54.2%"),
                    ],
                    "unit": "percent (HTTP 429)",
                    "annotation": "429 rate climbs as request_rate exceeds GLOBAL_RATE_LIMIT (15,000 req/min). Not a backend error — gateway is the bottleneck.",
                },
                "latency_p99": {
                    "values": [
                        ("2026-04-12T08:53:00Z", "15ms"),
                        ("2026-04-12T08:58:00Z", "16ms"),
                        ("2026-04-12T09:00:00Z", "19ms"),
                        ("2026-04-12T09:02:00Z", "21ms"),
                        ("2026-04-12T09:04:00Z", "22ms"),
                    ],
                    "unit": "milliseconds",
                    "annotation": "Minimal latency increase on gateway itself — 429s returned fast. Product-service upstream contributing slight increase.",
                },
                "cpu": {
                    "values": [
                        ("2026-04-12T08:53:00Z", "9%"),
                        ("2026-04-12T08:58:00Z", "11%"),
                        ("2026-04-12T09:00:00Z", "19%"),
                        ("2026-04-12T09:02:00Z", "26%"),
                        ("2026-04-12T09:04:00Z", "29%"),
                    ],
                    "unit": "percent",
                    "annotation": "CPU rising from connection overhead. Lower than a DDoS because per-connection processing is heavier (full HTTP sessions vs single-shot attack packets).",
                },
            },
            "product-service": {
                "cpu": {
                    "values": [
                        ("2026-04-12T08:53:00Z", "18%"),
                        ("2026-04-12T08:58:00Z", "22%"),
                        ("2026-04-12T09:00:00Z", "54%"),
                        ("2026-04-12T09:02:00Z", "81%"),
                        ("2026-04-12T09:04:00Z", "89%"),
                    ],
                    "unit": "percent",
                    "annotation": "CPU spiking as table-scan queries multiply. No query result cache — each requests hits DB.",
                },
                "error_rate": {
                    "values": [
                        ("2026-04-12T08:57:00Z", "0.8%"),
                        ("2026-04-12T09:00:00Z", "6.3%"),
                        ("2026-04-12T09:02:00Z", "14.6%"),
                        ("2026-04-12T09:04:00Z", "18.1%"),
                    ],
                    "unit": "percent",
                    "annotation": "503s from HikariCP pool exhaustion. DB connection pool (40 max) insufficient for concurrent load.",
                },
                "latency_p99": {
                    "values": [
                        ("2026-04-12T08:57:00Z", "94ms"),
                        ("2026-04-12T09:00:00Z", "285ms"),
                        ("2026-04-12T09:02:00Z", "492ms"),
                        ("2026-04-12T09:04:00Z", "620ms"),
                    ],
                    "unit": "milliseconds",
                    "annotation": "Latency degrading from DB pool contention + full table scan on products(sale=true). Missing index on sale column.",
                },
                "cache_hit_rate": {
                    "values": [
                        ("2026-04-12T08:57:00Z", "89%"),
                        ("2026-04-12T08:58:30Z", "62%"),
                        ("2026-04-12T09:00:00Z", "38%"),
                        ("2026-04-12T09:02:00Z", "29%"),
                        ("2026-04-12T09:04:00Z", "27%"),
                    ],
                    "unit": "percent",
                    "annotation": "Cache hit rate collapsed. New query params (?sale=true, ?sale=true&category=*) generate cache keys not present in warm cache — all fall through to DB.",
                },
            },
        }

        self.dependency_map = {
            "api-gateway": {
                "depends_on": ["product-service", "order-service", "marketing-campaign-service"],
                "depended_by": [],
            },
            "product-service": {
                "depends_on": ["redis-cache"],
                "depended_by": ["api-gateway"],
            },
            "order-service": {
                "depends_on": ["redis-cache"],
                "depended_by": ["api-gateway"],
            },
            "marketing-campaign-service": {
                "depends_on": [],
                "depended_by": ["api-gateway"],
            },
            "redis-cache": {
                "depends_on": [],
                "depended_by": ["product-service", "order-service"],
            },
        }

        self.recent_changes = {
            "marketing-campaign-service": [
                {
                    "timestamp": "2026-04-12T08:58:00Z",
                    "service": "marketing-campaign-service",
                    "description": "Deployed v1.4.0 — spring-flash-sale-2026 campaign activation",
                    "changelog": "Activated flash sale campaign. Sends push notifications to 2.1M mobile subscribers and email to 800K users. Deep-link target: /api/products?sale=true. Audience interaction expected within 2-15 minutes post-send.",
                },
            ],
            "api-gateway": [
                {
                    "timestamp": "2026-04-09T11:00:00Z",
                    "service": "api-gateway",
                    "description": "Deployed v5.2.0",
                    "changelog": "Minor dependency updates and security patches. Rate limit configuration unchanged from initial capacity planning values.",
                },
            ],
            "product-service": [
                {
                    "timestamp": "2026-04-07T15:00:00Z",
                    "service": "product-service",
                    "description": "Deployed v4.3.2",
                    "changelog": "Added sale_price and discount_pct fields to product catalog response. Added GET /api/products?sale=true filter endpoint. DB index on (sale) column not yet created — tracked in PROD-4821.",
                },
            ],
        }

        self.runbooks = {
            "api-gateway": (
                "## Runbook: api-gateway\n\n"
                "### 429 Too Many Requests\n\n"
                "1. **Differentiate DDoS from organic spike**\n"
                "   - query_metrics request_rate shape: gradual multi-minute ramp = organic; sub-90s cliff = attack.\n"
                "   - query_logs unique IP count: >1K unique IPs for 15K req/min = organic crowd; <50 IPs = attack.\n"
                "   - query_logs user-agents: real browsers (Chrome/Safari/Firefox) = organic; python-requests/curl/Go = bots.\n"
                "   - check_recent_changes: any marketing or campaign events scheduled?\n\n"
                "2. **If organic traffic spike (campaign / viral event)**\n"
                "   - Raise global rate limit immediately: `kubectl set env deployment/api-gateway GLOBAL_RATE_LIMIT=40000`\n"
                "   - Rolling restart to apply: `kubectl rollout restart deployment/api-gateway`\n"
                "   - Scale api-gateway pods: `kubectl scale deployment/api-gateway --replicas=6`\n"
                "   - Scale overloaded upstreams: `kubectl scale deployment/product-service --replicas=8`\n"
                "   - Check product-service cache hit rate — if low, pre-warm sale=true cache keys.\n\n"
                "3. **Post-incident**\n"
                "   - Add rate-limit capacity review to campaign pre-launch checklist.\n"
                "   - Configure HPA on api-gateway and product-service based on request_rate.\n\n"
                "### Rollback\n"
                "   `kubectl rollout undo deployment/api-gateway`\n"
            ),
            "rate-limit": (
                "## Runbook: Rate Limit Tuning\n\n"
                "Current config (as of last deploy):\n"
                "  GLOBAL_RATE_LIMIT: 15,000 req/min  ← set during initial capacity planning\n"
                "  PER_IP_RATE_LIMIT: 100 req/s\n\n"
                "To increase for traffic event:\n"
                "  kubectl set env deployment/api-gateway GLOBAL_RATE_LIMIT=40000\n"
                "  kubectl rollout restart deployment/api-gateway\n\n"
                "Note: GLOBAL_RATE_LIMIT was sized for ~1,200 req/min baseline + 10x headroom.\n"
                "Campaign traffic can exceed this by 8-15x baseline.\n"
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

    def get_relevant_tools(self) -> list:
        return [
            "query_metrics:api-gateway:request_rate",
            "query_logs:api-gateway",
            "check_recent_changes:marketing-campaign-service",
            "get_service_status:api-gateway",
        ]

    def get_tool_descriptions(self) -> dict:
        return {
            "query_logs": {
                "services": list(self.log_entries.keys()),
                "severity_options": ["all", "error", "warning", "info"],
            },
            "query_metrics": {
                "services": list(self.metrics.keys()),
                "metrics": ["request_rate", "error_rate", "latency_p99", "cpu", "cache_hit_rate"],
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

        # Correctly identifies legit traffic / campaign as root cause (0.30)
        legit_match = any(
            kw in root_cause_text
            for kw in ["flash sale", "campaign", "marketing", "legitimate traffic",
                       "organic traffic", "traffic spike", "traffic surge",
                       "rate limit too low", "rate limit not updated",
                       "global_rate_limit", "subscriber", "push notification", "email blast"]
        )
        if legit_match:
            score += 0.30

        # Does NOT incorrectly diagnose as DDoS (negative signal handled by no-bonus, not penalty)
        # Mentions campaign-specific technical detail — version, subscriber count, or rate limit value (0.20)
        detail_match = any(
            kw in root_cause_text
            for kw in ["marketing-campaign", "v1.4.0",
                       "15,000", "15000", "rate limit config", "rate limit not",
                       "rate limit was not", "campaign activation",
                       "2.1m", "800k", "8-12x", "8x traffic", "12x traffic"]
        )
        if detail_match:
            score += 0.20

        # Affected service is api-gateway (0.15)
        if affected == "api-gateway":
            score += 0.15

        # Recommendation is to raise rate limit / scale out (0.15)
        rec_match = any(
            kw in recommendation_text
            for kw in ["increase rate limit", "raise rate limit", "update rate limit",
                       "scale", "horizontal", "replicas", "global_rate_limit",
                       "kubectl scale", "auto-scal"]
        )
        if rec_match:
            score += 0.15

        # Efficiency bonus (0.10)
        if step_count <= 5:
            score += 0.10
        elif step_count <= 8:
            score += 0.05

        # No destructive recommendation (0.10)
        destructive = any(
            kw in recommendation_text
            for kw in ["block ip", "ban ip", "blacklist", "drop database",
                       "disable campaign", "kill campaign", "truncate"]
        )
        if not destructive:
            score += 0.10

        root_cause_correct = legit_match and detail_match
        recommendation_correct = rec_match

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
                e for e in entries
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
        for name, data in svc_metrics.items():
            if metric in name.lower() or name.lower() in metric:
                return self._format_metrics(name, data)
        return f"No matching metric '{metric}' for service '{service}'."

    def _handle_dependency_map(self, parameters: dict) -> str:
        service = parameters.get("service", "")
        if service and service in self.dependency_map:
            return self._format_dependency_map({service: self.dependency_map[service]})
        return self._format_dependency_map(self.dependency_map)

    def _handle_runbook(self, parameters: dict) -> str:
        topic = parameters.get("topic", "").lower()
        for key, value in self.runbooks.items():
            if topic and topic in key.lower():
                return self._format_runbook(value)
        return self._format_runbook(self.runbooks.get("api-gateway", ""))

    def _handle_recent_changes(self, parameters: dict) -> str:
        service = parameters.get("service", "")
        if service:
            changes = self.recent_changes.get(service)
            if changes is None:
                return f"No recent changes found for service '{service}'."
            return self._format_changes(changes)
        all_changes = []
        for changes in self.recent_changes.values():
            all_changes.extend(changes)
        all_changes.sort(key=lambda c: c["timestamp"], reverse=True)
        return self._format_changes(all_changes)
