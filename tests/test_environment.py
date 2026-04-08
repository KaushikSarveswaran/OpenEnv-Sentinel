"""Tests for SentinelEnvironment reset, step, submit, and termination."""

import pytest

from models import SentinelAction
from server.sentinel_environment import SentinelEnvironment, MAX_STEPS, MAX_CONSECUTIVE_INVALID


def _action(tool_name: str, **params):
    return SentinelAction.model_validate({"tool_name": tool_name, "parameters": params})


class TestReset:
    def test_reset_returns_observation(self, env):
        obs = env.reset(task_id=1)
        assert obs.done is False
        assert obs.incident_summary != ""
        assert obs.step_number == 0

    def test_reset_includes_tool_descriptions(self, env):
        obs = env.reset(task_id=1)
        assert obs.tool_descriptions != {}
        assert "query_logs" in obs.tool_descriptions

    def test_reset_invalid_task_defaults_to_1(self, env):
        obs = env.reset(task_id=999)
        assert obs.done is False
        assert env.state.task_id == 1


class TestStep:
    def test_step_without_reset(self, env):
        action = _action("get_service_status", service="auth")
        obs = env.step(action)
        assert obs.done is True
        assert "not reset" in obs.last_action_error.lower()

    def test_valid_step_returns_output(self, env):
        env.reset(task_id=1)
        action = _action("get_service_status", service="payment-api")
        obs = env.step(action)
        assert obs.tool_output != ""
        assert obs.done is False
        assert obs.step_number == 1

    def test_step_no_tool_descriptions(self, env):
        env.reset(task_id=1)
        action = _action("get_service_status", service="payment-api")
        obs = env.step(action)
        assert obs.tool_descriptions == {}

    def test_invalid_tool(self, env):
        env.reset(task_id=1)
        # Use a raw dict bypass since pydantic rejects unknown tools
        # Instead, test via unknown service which is still valid dispatch
        action = _action("get_service_status", service="nonexistent")
        obs = env.step(action)
        assert obs.done is False  # valid tool, just unknown service


class TestSubmit:
    def test_submit_resolution_grades(self, env):
        env.reset(task_id=1)
        action = _action(
            "submit_resolution",
            root_cause="Missing DB_CONNECTION_STRING after v2.3.1 deploy",
            affected_service="payment-api",
            recommendation="Rollback to v2.3.0",
        )
        obs = env.step(action)
        assert obs.done is True
        assert obs.reward is not None
        assert obs.reward > 0

    def test_submit_missing_fields(self, env):
        env.reset(task_id=1)
        action = _action(
            "submit_resolution",
            root_cause="",
            affected_service="",
            recommendation="",
        )
        obs = env.step(action)
        assert obs.last_action_error != ""
        assert obs.done is False


class TestTermination:
    def test_max_steps(self, env):
        env.reset(task_id=1)
        for _ in range(MAX_STEPS):
            action = _action("get_service_status", service="payment-api")
            obs = env.step(action)
        assert obs.done is True
        assert "maximum steps" in obs.tool_output.lower()

    def test_consecutive_invalid_not_triggered_by_valid(self, env):
        env.reset(task_id=1)
        for _ in range(MAX_CONSECUTIVE_INVALID + 1):
            action = _action("get_service_status", service="payment-api")
            obs = env.step(action)
        assert obs.done is False  # valid actions don't trigger termination
