"""Task 4 — The DDoS Attack: api-gateway rate-limiting due to a volumetric DDoS."""

import re

from .base import BaseScenario


class DDoSAttackScenario(BaseScenario):
    """api-gateway 429s caused by a DDoS — high volume from a small set of IPs
    targeting POST /api/login (credential-stuffing pattern)."""

    def __init__(self) -> None:
        self.incident_text = (
            "CRITICAL: api-gateway rejection rate spiked from 10% to 52%. "
            "Customers reporting inability to log in. HTTP 429 Too Many Requests. "
            "Started 7 minutes ago."
        )

        self.services = {
            "api-gateway": {
                "name": "api-gateway",
                "status": "DEGRADED",
                "error_rate": "52%",
                "uptime": "99.8% (30d)",
                "last_deploy": "v5.2.0 deployed 3 days ago",
                "restarts": 0,
                "latency_p99": "18ms",
                "connections": "18,400 active (normal: ~1,200)",
            },
            "auth-service": {
                "name": "auth-service",
                "status": "DEGRADED",
                "error_rate": "3.1%",
                "uptime": "99.99% (30d)",
                "last_deploy": "v3.4.1 deployed 6 days ago",
                "restarts": 0,
                "latency_p99": "420ms",
                "connections": "N/A",
            },
            "user-service": {
                "name": "user-service",
                "status": "HEALTHY",
                "error_rate": "0.3%",
                "uptime": "99.99% (30d)",
                "last_deploy": "v2.0.8 deployed 4 days ago",
                "latency_p99": "40ms",
            },
            "waf-service": {
                "name": "waf-service",
                "status": "HEALTHY",
                "error_rate": "0%",
                "uptime": "99.999% (30d)",
                "last_deploy": "v1.1.0 deployed 10 days ago",
            },
            "redis-cache": {
                "name": "redis-cache",
                "status": "HEALTHY",
                "error_rate": "0%",
                "uptime": "99.999% (30d)",
                "connections": "312 active (normal: ~48) — auth-service brute-force lockout checks",
            },
        }

        self.log_entries = {
            "api-gateway": [
                # Access log style — Envoy proxy format: [timestamp] IP method path status rt=Xms ua="..."
                {
                    "timestamp": "2026-04-12T08:37:02.114Z",
                    "level": "WARN",
                    "message": '185.220.101.14 "POST /api/login HTTP/1.1" 200 rt=11ms ua="python-requests/2.28.1" — per-IP rate: 18 req/s',
                    "source": "envoy.access_log",
                },
                {
                    "timestamp": "2026-04-12T08:37:02.198Z",
                    "level": "WARN",
                    "message": '185.220.101.14 "POST /api/login HTTP/1.1" 200 rt=9ms ua="python-requests/2.28.1" — per-IP rate: 34 req/s',
                    "source": "envoy.access_log",
                },
                {
                    "timestamp": "2026-04-12T08:37:02.881Z",
                    "level": "WARN",
                    "message": '185.220.101.22 "POST /api/login HTTP/1.1" 200 rt=12ms ua="python-requests/2.28.1" — per-IP rate: 21 req/s',
                    "source": "envoy.access_log",
                },
                {
                    "timestamp": "2026-04-12T08:37:03.004Z",
                    "level": "WARN",
                    "message": '45.142.212.100 "POST /api/login HTTP/1.1" 200 rt=10ms ua="Go-http-client/1.1" — per-IP rate: 29 req/s',
                    "source": "envoy.access_log",
                },
                {
                    "timestamp": "2026-04-12T08:37:03.112Z",
                    "level": "WARN",
                    "message": '45.142.212.101 "POST /api/login HTTP/1.1" 200 rt=8ms ua="Go-http-client/1.1" — per-IP rate: 31 req/s',
                    "source": "envoy.access_log",
                },
                {
                    "timestamp": "2026-04-12T08:37:45.002Z",
                    "level": "WARN",
                    "message": "Per-IP rate limit threshold (100 req/s) approaching for 185.220.101.14: current 87 req/s",
                    "source": "ratelimiter.RateLimiter.check(RateLimiter.java:88)",
                },
                {
                    "timestamp": "2026-04-12T08:38:00.321Z",
                    "level": "ERROR",
                    "message": '185.220.101.14 "POST /api/login HTTP/1.1" 429 rt=2ms ua="python-requests/2.28.1" — per-IP rate limit exceeded (114 req/s > 100 req/s)',
                    "source": "ratelimiter.RateLimiter.enforce(RateLimiter.java:104)",
                },
                {
                    "timestamp": "2026-04-12T08:38:00.334Z",
                    "level": "ERROR",
                    "message": '185.220.101.22 "POST /api/login HTTP/1.1" 429 rt=2ms ua="python-requests/2.28.1" — per-IP rate limit exceeded (109 req/s > 100 req/s)',
                    "source": "ratelimiter.RateLimiter.enforce(RateLimiter.java:104)",
                },
                {
                    "timestamp": "2026-04-12T08:38:00.341Z",
                    "level": "ERROR",
                    "message": '45.142.212.100 "POST /api/login HTTP/1.1" 429 rt=1ms ua="Go-http-client/1.1" — per-IP rate limit exceeded (118 req/s > 100 req/s)',
                    "source": "ratelimiter.RateLimiter.enforce(RateLimiter.java:104)",
                },
                {
                    "timestamp": "2026-04-12T08:38:02.005Z",
                    "level": "ERROR",
                    "message": '193.32.162.55 "POST /api/login HTTP/1.1" 429 rt=1ms ua="curl/7.88.1" — per-IP rate limit exceeded (103 req/s > 100 req/s)',
                    "source": "ratelimiter.RateLimiter.enforce(RateLimiter.java:104)",
                },
                {
                    "timestamp": "2026-04-12T08:38:04.110Z",
                    "level": "ERROR",
                    "message": '91.108.4.200 "POST /api/login HTTP/1.1" 429 rt=1ms ua="curl/7.88.1" — per-IP rate limit exceeded',
                    "source": "ratelimiter.RateLimiter.enforce(RateLimiter.java:104)",
                },
                {
                    "timestamp": "2026-04-12T08:38:06.880Z",
                    "level": "ERROR",
                    "message": '198.54.117.10 "POST /api/login HTTP/1.1" 429 rt=2ms ua="Scrapy/2.9.0 (+https://scrapy.org)" — per-IP rate limit exceeded',
                    "source": "ratelimiter.RateLimiter.enforce(RateLimiter.java:104)",
                },
                {
                    "timestamp": "2026-04-12T08:38:30.001Z",
                    "level": "INFO",
                    "message": (
                        "60s traffic window report: 18,420 total requests. "
                        "Unique IPs: 31 (normal: ~900/min). "
                        "Top-20 IPs account for 17,140 requests (93.1%). "
                        "Endpoint breakdown: POST /api/login 98.7%, GET /api/health 1.1%, other 0.2%. "
                        "User-agents: python-requests 41%, Go-http-client 33%, curl 19%, Scrapy 6%."
                    ),
                    "source": "metrics.TrafficAnalyzer.periodicReport(TrafficAnalyzer.java:89)",
                },
                {
                    "timestamp": "2026-04-12T08:39:00.002Z",
                    "level": "WARN",
                    "message": "Global connection count 17,400 approaching soft-limit 20,000. Attacker IPs maintaining persistent keep-alive connections.",
                    "source": "netio.ConnectionManager.warn(ConnectionManager.java:212)",
                },
                {
                    "timestamp": "2026-04-12T08:41:00.003Z",
                    "level": "ERROR",
                    "message": (
                        "Global rate cap 18,500/20,000 req/min. "
                        "Collateral damage: legitimate logins from real users also receiving 429 "
                        "as global cap approaches ceiling. Estimated legit traffic: ~1,720 req/min."
                    ),
                    "source": "ratelimiter.GlobalLimiter.check(GlobalLimiter.java:34)",
                },
            ],
            "auth-service": [
                {
                    "timestamp": "2026-04-12T08:37:10Z",
                    "level": "WARN",
                    "message": "Unusual login attempt pattern detected: 847 failed attempts in last 60s from 14 source IPs. Normal baseline: ~12 failed/min.",
                    "source": "auth.AnomalyDetector.evaluate(AnomalyDetector.java:55)",
                },
                {
                    "timestamp": "2026-04-12T08:37:22Z",
                    "level": "WARN",
                    "message": "Brute-force lockout triggered for user admin@corp.example.com (10 consecutive failures from 185.220.101.14). Lockout key written to Redis.",
                    "source": "auth.LockoutPolicy.enforce(LockoutPolicy.java:78)",
                },
                {
                    "timestamp": "2026-04-12T08:37:31Z",
                    "level": "WARN",
                    "message": "Brute-force lockout triggered for user j.smith@corp.example.com (10 consecutive failures from 45.142.212.100). Lockout key written to Redis.",
                    "source": "auth.LockoutPolicy.enforce(LockoutPolicy.java:78)",
                },
                {
                    "timestamp": "2026-04-12T08:38:00Z",
                    "level": "ERROR",
                    "message": "CPU throttling detected: bcrypt verification backlog 340 requests queued. Worker threads: 32/32 busy. bcrypt cost factor 12 → ~300ms/check.",
                    "source": "auth.PasswordVerifier.checkQueue(PasswordVerifier.java:93)",
                },
                {
                    "timestamp": "2026-04-12T08:38:15Z",
                    "level": "INFO",
                    "message": "Credential analysis last 5min: 6,814 login attempts received. Failed: 6,598 (96.8%). Unique usernames attempted: 5,412 (dictionary pattern). Unique source IPs: 18.",
                    "source": "auth.AuditLogger.summarize(AuditLogger.java:120)",
                },
                {
                    "timestamp": "2026-04-12T08:38:40Z",
                    "level": "WARN",
                    "message": "Redis INCR ops/sec: 2,840 (normal: ~40). Elevated from lockout-key creation and rate-limit counters.",
                    "source": "auth.RedisRateLimitStore.observe(RedisRateLimitStore.java:44)",
                },
                {
                    "timestamp": "2026-04-12T08:41:00Z",
                    "level": "WARN",
                    "message": "Auth service p99 latency 420ms (baseline: 45ms). Degradation caused by bcrypt thread pool saturation from attack volume.",
                    "source": "auth.HealthMonitor.report(HealthMonitor.java:33)",
                },
            ],
            "waf-service": [
                {
                    "timestamp": "2026-04-12T08:38:05Z",
                    "level": "WARN",
                    "message": "Threat signature match: IPs 185.220.101.0/24 and 45.142.212.0/24 are known Tor exit nodes / proxy ranges. Auto-block threshold set at 500 req/min per /24 subnet — current: 4,840 req/min (threshold not triggered for subnet blocks, only per-IP).",
                    "source": "waf.ThreatIntelFeed.evaluate(ThreatIntelFeed.java:67)",
                },
                {
                    "timestamp": "2026-04-12T08:39:10Z",
                    "level": "WARN",
                    "message": "Alert: POST /api/login attack score 94/100 (volumetric + credential-stuffing pattern + known-bad ASNs). Awaiting operator action to push block rules.",
                    "source": "waf.AttackScorer.score(AttackScorer.java:88)",
                },
            ],
        }

        self.metrics = {
            "api-gateway": {
                "request_rate": {
                    "values": [
                        ("2026-04-12T08:33:00Z", "1,183 req/min"),
                        ("2026-04-12T08:34:00Z", "1,196 req/min"),
                        ("2026-04-12T08:35:00Z", "1,209 req/min"),
                        ("2026-04-12T08:36:00Z", "1,191 req/min"),
                        ("2026-04-12T08:36:30Z", "1,204 req/min"),
                        ("2026-04-12T08:37:00Z", "4,852 req/min"),   # attack onset — vertical cliff
                        ("2026-04-12T08:37:30Z", "9,310 req/min"),
                        ("2026-04-12T08:38:00Z", "14,820 req/min"),
                        ("2026-04-12T08:38:30Z", "17,650 req/min"),
                        ("2026-04-12T08:39:00Z", "18,200 req/min"),
                        ("2026-04-12T08:40:00Z", "18,420 req/min"),
                        ("2026-04-12T08:41:00Z", "18,510 req/min"),
                    ],
                    "unit": "requests/min",
                    "annotation": "Zero-to-peak in <90s starting 08:37:00Z. No deploy, no config change, no traffic event at that time. Shape is characteristic of a scripted attack launch.",
                },
                "error_rate": {
                    "values": [
                        ("2026-04-12T08:33:00Z", "0.8%"),
                        ("2026-04-12T08:36:00Z", "0.9%"),
                        ("2026-04-12T08:36:30Z", "0.9%"),
                        ("2026-04-12T08:37:00Z", "9.4%"),
                        ("2026-04-12T08:37:30Z", "22.1%"),
                        ("2026-04-12T08:38:00Z", "39.8%"),
                        ("2026-04-12T08:38:30Z", "47.3%"),
                        ("2026-04-12T08:39:00Z", "50.5%"),
                        ("2026-04-12T08:40:00Z", "51.9%"),
                        ("2026-04-12T08:41:00Z", "52.1%"),
                    ],
                    "unit": "percent (HTTP 429)",
                    "annotation": "429 rate mirrors request_rate step-function. Serving ~8,900 legit req/min; blocking ~9,600 attack req/min.",
                },
                "latency_p99": {
                    "values": [
                        ("2026-04-12T08:33:00Z", "14ms"),
                        ("2026-04-12T08:36:00Z", "14ms"),
                        ("2026-04-12T08:37:00Z", "15ms"),
                        ("2026-04-12T08:38:00Z", "17ms"),
                        ("2026-04-12T08:39:00Z", "18ms"),
                        ("2026-04-12T08:41:00Z", "18ms"),
                    ],
                    "unit": "milliseconds",
                    "annotation": "p99 barely moved — 429s returned in <2ms by rate limiter before hitting any backend. Backend services unaffected.",
                },
                "cpu": {
                    "values": [
                        ("2026-04-12T08:33:00Z", "8%"),
                        ("2026-04-12T08:36:00Z", "9%"),
                        ("2026-04-12T08:37:00Z", "22%"),
                        ("2026-04-12T08:38:00Z", "34%"),
                        ("2026-04-12T08:39:00Z", "38%"),
                        ("2026-04-12T08:41:00Z", "41%"),
                    ],
                    "unit": "percent",
                    "annotation": "CPU climbing from TCP accept loop overhead processing 18K+ connections/min, even though most are rejected quickly.",
                },
            },
            "auth-service": {
                "cpu": {
                    "values": [
                        ("2026-04-12T08:33:00Z", "12%"),
                        ("2026-04-12T08:36:00Z", "13%"),
                        ("2026-04-12T08:37:00Z", "41%"),
                        ("2026-04-12T08:38:00Z", "88%"),
                        ("2026-04-12T08:39:00Z", "91%"),
                        ("2026-04-12T08:41:00Z", "93%"),
                    ],
                    "unit": "percent",
                    "annotation": "CPU near saturation from bcrypt password hashing. Attack requests that bypass per-IP limiter still get bcrypt-checked. bcrypt cost=12 takes ~300ms CPU per attempt.",
                },
                "error_rate": {
                    "values": [
                        ("2026-04-12T08:33:00Z", "0.5%"),
                        ("2026-04-12T08:37:00Z", "1.1%"),
                        ("2026-04-12T08:38:00Z", "2.4%"),
                        ("2026-04-12T08:40:00Z", "3.1%"),
                        ("2026-04-12T08:41:00Z", "3.1%"),
                    ],
                    "unit": "percent",
                    "annotation": "Errors are 503s from bcrypt thread pool overflow, not crashes. Most attack traffic stopped by api-gateway before reaching auth-service.",
                },
                "login_failure_rate": {
                    "values": [
                        ("2026-04-12T08:33:00Z", "1.8%"),
                        ("2026-04-12T08:36:00Z", "2.0%"),
                        ("2026-04-12T08:37:00Z", "61.4%"),
                        ("2026-04-12T08:38:00Z", "94.2%"),
                        ("2026-04-12T08:39:00Z", "96.8%"),
                        ("2026-04-12T08:41:00Z", "96.8%"),
                    ],
                    "unit": "percent of login attempts",
                    "annotation": "96.8% failure rate strongly indicates credential stuffing — attacker cycling username:password pairs from a leaked list.",
                },
            },
            "redis-cache": {
                "connections": {
                    "values": [
                        ("2026-04-12T08:33:00Z", "48"),
                        ("2026-04-12T08:36:00Z", "51"),
                        ("2026-04-12T08:37:00Z", "128"),
                        ("2026-04-12T08:38:00Z", "274"),
                        ("2026-04-12T08:39:00Z", "308"),
                        ("2026-04-12T08:41:00Z", "312"),
                    ],
                    "unit": "active connections",
                    "annotation": "Redis connection spike driven by auth-service writing lockout keys and rate-limit counters for each attacked account.",
                },
            },
        }

        self.dependency_map = {
            "api-gateway": {
                "depends_on": ["auth-service", "user-service", "waf-service"],
                "depended_by": [],
            },
            "auth-service": {
                "depends_on": ["redis-cache"],
                "depended_by": ["api-gateway"],
            },
            "user-service": {
                "depends_on": ["redis-cache"],
                "depended_by": ["api-gateway"],
            },
            "waf-service": {
                "depends_on": [],
                "depended_by": ["api-gateway"],
            },
            "redis-cache": {
                "depends_on": [],
                "depended_by": ["auth-service", "user-service"],
            },
        }

        self.recent_changes = {
            "api-gateway": [
                {
                    "timestamp": "2026-04-09T11:00:00Z",
                    "service": "api-gateway",
                    "description": "Deployed v5.2.0",
                    "changelog": "Bumped default per-IP rate limit from 80 req/s to 100 req/s. No changes to global rate cap or WAF integration.",
                },
            ],
            "waf-service": [
                {
                    "timestamp": "2026-04-02T09:00:00Z",
                    "service": "waf-service",
                    "description": "Deployed v1.1.0",
                    "changelog": "Updated Tor exit node and known-proxy IP lists. Auto-block currently configured per-IP only (threshold: 500 req/min). Subnet-level blocking requires manual operator push.",
                },
            ],
        }

        self.runbooks = {
            "api-gateway": (
                "## Runbook: api-gateway\n\n"
                "### 429 Too Many Requests\n\n"
                "1. **Differentiate DDoS from legitimate spike**\n"
                "   - query_metrics request_rate: vertical cliff (<2min to peak) = attack; gradual ramp (5-10min) = organic.\n"
                "   - query_logs: examine IP diversity. <50 unique IPs for >10K req/min = attack. >1K unique IPs = organic.\n"
                "   - query_logs: check user-agents. python-requests / curl / Go-http-client at scale = bots.\n"
                "   - query_metrics auth-service login_failure_rate: >80% failures = credential stuffing.\n\n"
                "2. **If DDoS / credential stuffing**\n"
                "   - Push IP block list to waf-service: `kubectl exec -it waf-service -- block-ips --file /tmp/offenders.txt`\n"
                "   - Enable subnet-level blocking for offending /24 ranges in waf-service.\n"
                "   - Reduce per-IP limit temporarily: `kubectl set env deployment/api-gateway RATE_LIMIT_PER_IP=20`\n"
                "   - Enable CAPTCHA on POST /api/login: feature flag `login.captcha.enabled=true`.\n"
                "   - Escalate to #security-oncall immediately.\n\n"
                "3. **If legitimate spike**\n"
                "   - Raise GLOBAL_RATE_LIMIT: `kubectl set env deployment/api-gateway GLOBAL_RATE_LIMIT=40000`\n"
                "   - Scale horizontally: `kubectl scale deployment/api-gateway --replicas=6`\n\n"
                "### Rollback\n"
                "   `kubectl rollout undo deployment/api-gateway`\n"
            ),
            "ddos": (
                "## Runbook: DDoS / Credential Stuffing Mitigation\n\n"
                "### Indicators\n"
                "- Few source IPs (< 50) driving >80% of traffic\n"
                "- Single endpoint targeted (POST /api/login, /api/register)\n"
                "- Bot user-agents: python-requests, curl, Go-http-client, Scrapy\n"
                "- auth-service login_failure_rate > 80%\n"
                "- Known-bad IP ranges (Tor exit nodes: 185.220.x.x, 45.142.x.x; proxies: 193.32.x.x)\n\n"
                "### Mitigation Steps\n"
                "1. Block offending IPs in waf-service (manual push required for subnet blocks).\n"
                "2. Engage upstream null-route for volumetric floods via NOC ticket.\n"
                "3. Add CAPTCHA to targeted endpoint.\n"
                "4. Force password reset for any accounts with successful logins during the window.\n"
                "5. File incident report with #security-oncall.\n"
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
            "query_metrics:api-gateway:error_rate",
            "query_logs:api-gateway",
            "get_service_status:api-gateway",
            "query_logs:auth-service",
            "query_metrics:auth-service:login_failure_rate",
        ]

    def get_tool_descriptions(self) -> dict:
        return {
            "query_logs": {
                "services": list(self.log_entries.keys()),
                "severity_options": ["all", "error", "warning", "info"],
            },
            "query_metrics": {
                "services": list(self.metrics.keys()),
                "metrics": ["request_rate", "error_rate", "latency_p99", "cpu", "login_failure_rate", "connections"],
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

        # Correctly identifies DDoS / malicious traffic (0.30)
        ddos_match = any(
            kw in root_cause_text
            for kw in ["ddos", "denial of service", "malicious", "credential stuffing",
                       "few ip", "small number of ip", "concentrated ip", "18 ip",
                       "bot", "attack", "volumetric"]
        )
        if ddos_match:
            score += 0.30

        # Mentions the targeted endpoint or IP concentration (0.20)
        detail_match = any(
            kw in root_cause_text
            for kw in ["post /api/login", "/api/login", "login endpoint",
                       "90%", "single endpoint", "ip concentration", "185.220", "45.142"]
        )
        if detail_match:
            score += 0.20

        # Affected service is api-gateway (0.15)
        if affected == "api-gateway":
            score += 0.15

        # Recommendation is to block IPs / engage WAF (0.15)
        rec_match = any(
            kw in recommendation_text
            for kw in ["block ip", "block the ip", "waf", "firewall", "null-route",
                       "ip block", "ban ip", "blacklist", "blocklist", "captcha",
                       "block offending", "block malicious"]
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
            for kw in ["drop database", "delete all", "truncate", "restart-all",
                       "increase rate limit", "disable rate limit", "remove rate limit"]
        )
        if not destructive:
            score += 0.10

        root_cause_correct = ddos_match and detail_match
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
        # Default: return api-gateway runbook
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
