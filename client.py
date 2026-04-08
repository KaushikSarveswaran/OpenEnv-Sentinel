"""SentinelEnv client — connects to the Sentinel environment server."""

from openenv.core import EnvClient, StepResult
from .models import SentinelAction, SentinelObservation, SentinelState


class SentinelEnv(EnvClient[SentinelAction, SentinelObservation, SentinelState]):
    """Client for the Sentinel SRE Incident Triage Environment."""

    def _step_payload(self, action: SentinelAction) -> dict:
        return {
            "tool_name": action.tool_name,
            "parameters": action.param_dict(),
        }

    def _parse_result(self, payload: dict) -> StepResult[SentinelObservation]:
        obs = SentinelObservation(**payload["observation"])
        return StepResult(
            observation=obs,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> SentinelState:
        return SentinelState(**payload)
