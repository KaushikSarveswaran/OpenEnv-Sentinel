"""Tests for tool dispatch and make_relevance_key."""

import pytest

from tools.registry import dispatch, make_relevance_key


class TestMakeRelevanceKey:
    def test_tool_with_service(self):
        assert make_relevance_key("query_logs", {"service": "auth"}) == "query_logs:auth"

    def test_tool_with_service_and_metric(self):
        key = make_relevance_key("query_metrics", {"service": "pg", "metric": "cpu"})
        assert key == "query_metrics:pg:cpu"

    def test_tool_with_topic(self):
        key = make_relevance_key("consult_runbook", {"topic": "connection pool"})
        assert key == "consult_runbook:connection pool"

    def test_tool_no_params(self):
        assert make_relevance_key("check_recent_changes", {}) == "check_recent_changes"

    def test_tool_empty_service(self):
        assert make_relevance_key("get_dependency_map", {"service": ""}) == "get_dependency_map"


class TestDispatch:
    def test_unknown_tool(self, task1):
        output, is_valid = dispatch("hack_server", {}, task1)
        assert is_valid is False
        assert "Unknown tool" in output

    def test_valid_tool(self, task1):
        output, is_valid = dispatch("get_service_status", {"service": "payment-api"}, task1)
        assert is_valid is True
        assert output != ""

    def test_submit_resolution_passthrough(self, task1):
        output, is_valid = dispatch("submit_resolution", {}, task1)
        assert is_valid is True
        assert output == ""
