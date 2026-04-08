"""Tests for typed action models and discriminated union."""

import pytest
from pydantic import ValidationError

from models import (
    SentinelAction,
    QueryLogsAction,
    SubmitResolutionAction,
    SentinelObservation,
)


class TestDeserialization:
    def test_query_logs(self):
        raw = {"tool_name": "query_logs", "parameters": {"service": "auth", "query": "error"}}
        action = SentinelAction.model_validate(raw)
        assert action.tool_name == "query_logs"
        assert action.param_dict() == {"service": "auth", "query": "error", "severity": "all"}

    def test_submit_resolution(self):
        raw = {
            "tool_name": "submit_resolution",
            "parameters": {"root_cause": "x", "affected_service": "y", "recommendation": "z"},
        }
        action = SentinelAction.model_validate(raw)
        assert action.param_dict()["root_cause"] == "x"

    def test_get_dependency_map_defaults(self):
        raw = {"tool_name": "get_dependency_map", "parameters": {}}
        action = SentinelAction.model_validate(raw)
        assert action.param_dict() == {"service": ""}


class TestInvalidRejection:
    def test_unknown_tool_name(self):
        raw = {"tool_name": "hack_server", "parameters": {}}
        with pytest.raises(ValidationError):
            SentinelAction.model_validate(raw)

    def test_missing_required_param(self):
        raw = {"tool_name": "query_logs", "parameters": {}}
        with pytest.raises(ValidationError):
            SentinelAction.model_validate(raw)


class TestDiscriminator:
    def test_schema_has_discriminator(self):
        schema = SentinelAction.model_json_schema()
        assert "$defs" in schema


class TestObservation:
    def test_tool_descriptions_default_empty(self):
        obs = SentinelObservation()
        assert obs.tool_descriptions == {}

    def test_tool_descriptions_populated(self):
        obs = SentinelObservation(tool_descriptions={"query_logs": {"services": ["a"]}})
        assert "query_logs" in obs.tool_descriptions
