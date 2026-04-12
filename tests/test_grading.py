"""Tests for per-task grading: perfect scores, partial credit, wrong service, destructive penalty."""

import pytest


class TestTask1Grading:
    def test_perfect_resolution(self, task1):
        result = task1.grade_resolution(
            {
                "root_cause": "Missing DB_CONNECTION_STRING env var after deploy v2.3.1",
                "affected_service": "payment-api",
                "recommendation": "Rollback to v2.3.0 or set the DB_CONNECTION_STRING env var",
            },
            step_count=3,
        )
        assert result["score"] >= 0.80

    def test_wrong_service(self, task1):
        result = task1.grade_resolution(
            {
                "root_cause": "Missing DB_CONNECTION_STRING env var after deploy v2.3.1",
                "affected_service": "order-service",
                "recommendation": "Rollback",
            },
            step_count=3,
        )
        # Should lose the affected_service points
        assert result["score"] <= 0.85

    def test_empty_resolution(self, task1):
        result = task1.grade_resolution(
            {"root_cause": "", "affected_service": "", "recommendation": ""},
            step_count=1,
        )
        assert result["score"] <= 0.20


class TestTask2Grading:
    def test_perfect_resolution(self, task2):
        result = task2.grade_resolution(
            {
                "root_cause": "inventory-service OOM memory leak from batch processing causing checkout-service timeout",
                "affected_service": "inventory-service",
                "recommendation": "Increase memory limit to 1Gi and reduce batch size or stream results",
            },
            step_count=4,
        )
        assert result["score"] >= 0.70

    def test_wrong_root_cause(self, task2):
        result = task2.grade_resolution(
            {
                "root_cause": "Network partition",
                "affected_service": "inventory-service",
                "recommendation": "Restart networking",
            },
            step_count=3,
        )
        assert result["score"] < 0.40


class TestTask3Grading:
    def test_perfect_resolution(self, task3):
        result = task3.grade_resolution(
            {
                "root_cause": "analytics-worker long-running query exhausted the connection pool, cascade to auth-service, user-profile-service, notification-service",
                "affected_service": "postgres-primary",
                "recommendation": "Kill the query and set statement_timeout, use read replica for analytics",
            },
            step_count=5,
        )
        assert result["score"] >= 0.70

    def test_blames_notification_deploy(self, task3):
        result = task3.grade_resolution(
            {
                "root_cause": "notification-service deploy v3.1 caused the failure",
                "affected_service": "notification-service",
                "recommendation": "Rollback notification-service",
            },
            step_count=3,
        )
        # Should score poorly — wrong root cause and wrong affected service
        assert result["score"] <= 0.20

    def test_partial_credit_pool_only(self, task3):
        result = task3.grade_resolution(
            {
                "root_cause": "postgres connection pool exhausted and full",
                "affected_service": "postgres-primary",
                "recommendation": "Increase pool size",
            },
            step_count=3,
        )
        # Pool identified but not analytics-worker
        assert 0.20 <= result["score"] <= 0.65


class TestTask4Grading:
    def test_perfect_resolution(self, task4):
        result = task4.grade_resolution(
            {
                "root_cause": "DDoS volumetric attack: 18 IPs account for 90.7% of traffic all targeting POST /api/login — credential stuffing",
                "affected_service": "api-gateway",
                "recommendation": "Block offending IPs via waf-service and enable auto-block for IPs exceeding 200 req/s",
            },
            step_count=4,
        )
        assert result["score"] >= 0.80
        assert result["root_cause_correct"] is True
        assert result["recommendation_correct"] is True

    def test_wrong_diagnosis_legit_traffic(self, task4):
        result = task4.grade_resolution(
            {
                "root_cause": "Legitimate traffic spike from campaign",
                "affected_service": "api-gateway",
                "recommendation": "Increase rate limit and scale horizontally",
            },
            step_count=4,
        )
        # Wrong root cause — should score low
        assert result["score"] <= 0.40
        assert result["root_cause_correct"] is False

    def test_destructive_recommendation_penalty(self, task4):
        result = task4.grade_resolution(
            {
                "root_cause": "DDoS attack from few malicious IPs targeting /api/login",
                "affected_service": "api-gateway",
                "recommendation": "Disable rate limit entirely to stop 429s",
            },
            step_count=4,
        )
        # Loses destructive penalty (0.10) and rec_match (0.15)
        vanilla = task4.grade_resolution(
            {
                "root_cause": "DDoS attack from few malicious IPs targeting /api/login",
                "affected_service": "api-gateway",
                "recommendation": "Block malicious IPs via waf",
            },
            step_count=4,
        )
        assert result["score"] < vanilla["score"]

    def test_wrong_affected_service(self, task4):
        result = task4.grade_resolution(
            {
                "root_cause": "DDoS from 18 IPs hitting POST /api/login",
                "affected_service": "auth-service",
                "recommendation": "Block IPs via waf-service",
            },
            step_count=4,
        )
        correct = task4.grade_resolution(
            {
                "root_cause": "DDoS from 18 IPs hitting POST /api/login",
                "affected_service": "api-gateway",
                "recommendation": "Block IPs via waf-service",
            },
            step_count=4,
        )
        # Loses the affected_service points (0.15) vs correct service
        assert result["score"] < correct["score"]

    def test_efficiency_bonus(self, task4):
        low_steps = task4.grade_resolution(
            {
                "root_cause": "DDoS attack: 18 IPs account for 90% of traffic on POST /api/login",
                "affected_service": "api-gateway",
                "recommendation": "Block offending IPs via WAF firewall",
            },
            step_count=4,
        )
        high_steps = task4.grade_resolution(
            {
                "root_cause": "DDoS attack: 18 IPs account for 90% of traffic on POST /api/login",
                "affected_service": "api-gateway",
                "recommendation": "Block offending IPs via WAF firewall",
            },
            step_count=15,
        )
        assert low_steps["score"] > high_steps["score"]


class TestTask5Grading:
    def test_perfect_resolution(self, task5):
        result = task5.grade_resolution(
            {
                "root_cause": "Legitimate flash sale traffic surge triggered by marketing campaign v1.4.0: 2.1M push + 800K email sent to subscribers. GLOBAL_RATE_LIMIT of 15,000 req/min was never updated for the campaign.",
                "affected_service": "api-gateway",
                "recommendation": "Raise GLOBAL_RATE_LIMIT to 40000 and scale api-gateway replicas horizontally",
            },
            step_count=4,
        )
        assert result["score"] >= 0.80
        assert result["root_cause_correct"] is True
        assert result["recommendation_correct"] is True

    def test_wrong_diagnosis_ddos(self, task5):
        result = task5.grade_resolution(
            {
                "root_cause": "DDoS attack from malicious IPs",
                "affected_service": "api-gateway",
                "recommendation": "Block IPs via WAF and enable firewall rules",
            },
            step_count=4,
        )
        # Wrong root cause — should score low, and destructive penalty applies
        assert result["score"] <= 0.30
        assert result["root_cause_correct"] is False

    def test_partial_credit_no_detail(self, task5):
        result = task5.grade_resolution(
            {
                "root_cause": "Legitimate traffic spike from a marketing campaign",
                "affected_service": "api-gateway",
                "recommendation": "Scale horizontally to handle load",
            },
            step_count=6,
        )
        # Legit match but no detail match (no campaign version / rate limit mention)
        assert result["root_cause_correct"] is False
        assert 0.30 <= result["score"] <= 0.80

    def test_wrong_affected_service(self, task5):
        result = task5.grade_resolution(
            {
                "root_cause": "Flash sale campaign v1.4.0 caused traffic surge, rate limit not updated (15000)",
                "affected_service": "marketing-campaign-service",
                "recommendation": "Increase rate limit and scale api-gateway replicas",
            },
            step_count=4,
        )
        # Loses affected_service points only
        correct = task5.grade_resolution(
            {
                "root_cause": "Flash sale campaign v1.4.0 caused traffic surge, rate limit not updated (15000)",
                "affected_service": "api-gateway",
                "recommendation": "Increase rate limit and scale api-gateway replicas",
            },
            step_count=4,
        )
        assert result["score"] < correct["score"]

    def test_efficiency_bonus(self, task5):
        low_steps = task5.grade_resolution(
            {
                "root_cause": "Flash sale campaign v1.4.0 triggered 8-12x traffic; GLOBAL_RATE_LIMIT not updated",
                "affected_service": "api-gateway",
                "recommendation": "Raise rate limit and scale horizontally",
            },
            step_count=3,
        )
        high_steps = task5.grade_resolution(
            {
                "root_cause": "Flash sale campaign v1.4.0 triggered 8-12x traffic; GLOBAL_RATE_LIMIT not updated",
                "affected_service": "api-gateway",
                "recommendation": "Raise rate limit and scale horizontally",
            },
            step_count=18,
        )
        assert low_steps["score"] > high_steps["score"]
