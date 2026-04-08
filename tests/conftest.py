"""Shared fixtures for Sentinel tests."""

import pytest

from scenarios.task1_smoking_gun import SmokingGunScenario
from scenarios.task2_upstream_culprit import UpstreamCulpritScenario
from scenarios.task3_cascading_failure import CascadingFailureScenario
from server.sentinel_environment import SentinelEnvironment


@pytest.fixture
def task1():
    return SmokingGunScenario()


@pytest.fixture
def task2():
    return UpstreamCulpritScenario()


@pytest.fixture
def task3():
    return CascadingFailureScenario()


@pytest.fixture
def env():
    return SentinelEnvironment()
