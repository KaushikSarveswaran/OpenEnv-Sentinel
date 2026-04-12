"""SentinelEnvironment — core OpenEnv Environment for SRE incident triage."""

import uuid
from typing import Any, Optional

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import Observation

from grading.grader import grade
from grading.rewards import compute_step_reward, _call_signature, _is_relevant
from models import SentinelAction, SentinelObservation, SentinelState
from scenarios.task1_smoking_gun import SmokingGunScenario
from scenarios.task2_upstream_culprit import UpstreamCulpritScenario
from scenarios.task3_cascading_failure import CascadingFailureScenario
from scenarios.task4_ddos_attack import DDoSAttackScenario
from scenarios.task5_flash_sale_spike import FlashSaleSpikeScenario
from tools.registry import AVAILABLE_TOOLS, dispatch, make_relevance_key

MAX_STEPS = 20
MAX_CONSECUTIVE_INVALID = 5

SCENARIOS = {
    1: SmokingGunScenario,
    2: UpstreamCulpritScenario,
    3: CascadingFailureScenario,
    4: DDoSAttackScenario,
    5: FlashSaleSpikeScenario,
}

TASK_NAMES = {
    1: "The Smoking Gun",
    2: "The Upstream Culprit",
    3: "The Cascading Failure",
    4: "The DDoS Attack",
    5: "The Flash Sale Spike",
}


class SentinelEnvironment(Environment):
    """OpenEnv Environment for SRE incident triage."""

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        super().__init__()
        self._scenario = None
        self._state = SentinelState()
        self._cumulative_reward: float = 0.0
        self._previous_calls: list[str] = []
        self._consecutive_invalid: int = 0

    # ── helpers ──────────────────────────────────────────────────────

    def _make_obs(
        self,
        *,
        tool_output: str = "",
        error: str = "",
        done: bool = False,
        reward: Optional[float] = None,
        tool_descriptions: Optional[dict] = None,
    ) -> SentinelObservation:
        return SentinelObservation(
            incident_summary=self._scenario.get_incident_summary() if self._scenario else "",
            tool_output=tool_output,
            available_tools=AVAILABLE_TOOLS,
            step_number=self._state.step_count,
            max_steps=MAX_STEPS,
            cumulative_reward=self._cumulative_reward,
            last_action_error=error,
            done=done,
            reward=reward,
            tool_descriptions=tool_descriptions or {},
        )

    def _handle_submit(self, params: dict, step_num: int) -> SentinelObservation:
        required = ("root_cause", "affected_service", "recommendation")
        missing = [f for f in required if not params.get(f)]
        if missing:
            return self._make_obs(
                error=f"submit_resolution requires: {', '.join(missing)}",
                done=False,
                reward=0.0,
            )

        self._consecutive_invalid = 0
        result = grade(self._scenario, params, step_num)
        self._state.resolution_submitted = True
        self._state.root_cause_correct = result["root_cause_correct"]
        self._state.recommendation_correct = result["recommendation_correct"]
        self._state.final_score = result["score"]
        self._state.tools_called.append("submit_resolution")

        return self._make_obs(
            tool_output=f"Resolution graded. Score: {result['score']:.4f}",
            done=True,
            reward=result["score"],
        )

    # ── Environment interface ────────────────────────────────────────

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> SentinelObservation:
        task_id = kwargs.get("task_id", 1)
        if task_id not in SCENARIOS:
            task_id = 1

        self._scenario = SCENARIOS[task_id]()
        self._cumulative_reward = 0.0
        self._previous_calls = []
        self._consecutive_invalid = 0

        self._state = SentinelState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            task_id=task_id,
            task_name=TASK_NAMES[task_id],
        )

        return self._make_obs(
            done=False,
            reward=None,
            tool_descriptions=self._scenario.get_tool_descriptions(),
        )

    def step(
        self,
        action: SentinelAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> SentinelObservation:
        if self._scenario is None:
            return SentinelObservation(
                incident_summary="",
                last_action_error="Environment not reset. Call reset() first.",
                done=True,
                reward=1e-3,
            )

        self._state.step_count += 1
        step_num = self._state.step_count

        tool_name = action.tool_name
        params = action.param_dict()

        # ── submit_resolution ───────────────────────────────────────
        if tool_name == "submit_resolution":
            return self._handle_submit(params, step_num)

        # ── regular tool dispatch ───────────────────────────────────
        output, is_valid = dispatch(tool_name, params, self._scenario)

        if not is_valid:
            self._consecutive_invalid += 1
        else:
            self._consecutive_invalid = 0

        # compute reward
        reward = compute_step_reward(
            tool_name,
            params,
            is_valid,
            self._scenario.get_relevant_tools(),
            self._previous_calls,
        )
        self._cumulative_reward += reward

        # track call
        sig = _call_signature(tool_name, params)
        self._previous_calls.append(sig)
        self._state.tools_called.append(f"{tool_name}({params})")

        # track relevant
        if is_valid and _is_relevant(tool_name, params, self._scenario.get_relevant_tools()):
            self._state.relevant_tools_called.append(f"{tool_name}({params})")

        # ── check termination ───────────────────────────────────────
        done = False
        error_msg = "" if is_valid else output

        if self._consecutive_invalid >= MAX_CONSECUTIVE_INVALID:
            done = True
            output = f"{output}\n\nEpisode terminated: {MAX_CONSECUTIVE_INVALID} consecutive invalid actions."
            self._state.final_score = 1e-3

        if step_num >= MAX_STEPS:
            done = True
            output = f"{output}\n\nEpisode terminated: maximum steps ({MAX_STEPS}) reached."
            self._state.final_score = 1e-3

        if done:
            reward = self._state.final_score

        return self._make_obs(
            tool_output=output,
            error=error_msg,
            done=done,
            reward=reward,
        )

    @property
    def state(self) -> SentinelState:
        return self._state
