"""Tests for per-task grading: perfect scores, partial credit, wrong service, destructive penalty."""

import pytest

from grading.rewards import compute_step_reward, REWARD_RELEVANT, REWARD_IRRELEVANT, REWARD_REPEATED, REWARD_INVALID, REWARD_STEP_COST


class TestComputeStepReward:
    RELEVANT_TOOLS = ["query_logs:auth-service", "get_service_status:payment-api"]

    def test_relevant_call(self):
        reward, breakdown = compute_step_reward(
            "query_logs", {"service": "auth-service"}, True, self.RELEVANT_TOOLS, []
        )
        assert reward == pytest.approx(REWARD_STEP_COST + REWARD_RELEVANT)
        assert breakdown.classification == "relevant"
        assert any(c.label == "relevant" for c in breakdown.components)
        assert any(c.label == "step_cost" for c in breakdown.components)
        assert "relevant" in breakdown.reason
        assert "auth-service" in breakdown.reason

    def test_irrelevant_call(self):
        reward, breakdown = compute_step_reward(
            "consult_runbook", {"topic": "dns"}, True, self.RELEVANT_TOOLS, []
        )
        assert reward == pytest.approx(REWARD_STEP_COST + REWARD_IRRELEVANT)
        assert breakdown.classification == "irrelevant"
        assert any(c.label == "irrelevant" for c in breakdown.components)
        assert "irrelevant" in breakdown.reason

    def test_repeated_call(self):
        sig = "query_logs:auth-service"
        reward, breakdown = compute_step_reward(
            "query_logs", {"service": "auth-service"}, True, self.RELEVANT_TOOLS, [sig]
        )
        assert reward == pytest.approx(REWARD_STEP_COST + REWARD_REPEATED)
        assert breakdown.classification == "repeated"
        assert any(c.label == "repeated" for c in breakdown.components)
        assert "repeated" in breakdown.reason

    def test_invalid_action(self):
        reward, breakdown = compute_step_reward(
            "bad_tool", {}, False, self.RELEVANT_TOOLS, []
        )
        assert reward == pytest.approx(REWARD_STEP_COST + REWARD_INVALID)
        assert breakdown.classification == "invalid"
        assert any(c.label == "invalid" for c in breakdown.components)
        assert "invalid" in breakdown.reason

    def test_components_sum_to_reward(self):
        reward, breakdown = compute_step_reward(
            "query_logs", {"service": "auth-service"}, True, self.RELEVANT_TOOLS, []
        )
        assert sum(c.value for c in breakdown.components) == pytest.approx(reward)


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
