"""Pydantic models for OpenEnv-Sentinel.

Typed discriminated union for actions — each tool has its own action + params class.
"""

from typing import Annotated, List, Literal, Optional, Union

from openenv.core.env_server.types import Action, Observation, State
from pydantic import BaseModel, Field, RootModel


# ── Parameter models ────────────────────────────────────────────────


class QueryLogsParams(BaseModel):
    service: str
    query: str = "all"
    severity: str = "all"


class QueryMetricsParams(BaseModel):
    service: str
    metric: str


class GetServiceStatusParams(BaseModel):
    service: str


class GetDependencyMapParams(BaseModel):
    service: str = ""


class ConsultRunbookParams(BaseModel):
    topic: str


class CheckRecentChangesParams(BaseModel):
    service: str = ""


class SubmitResolutionParams(BaseModel):
    root_cause: str
    affected_service: str
    recommendation: str


# ── Action models ───────────────────────────────────────────────────


class QueryLogsAction(Action):
    tool_name: Literal["query_logs"] = "query_logs"
    parameters: QueryLogsParams

    def param_dict(self) -> dict:
        return self.parameters.model_dump()


class QueryMetricsAction(Action):
    tool_name: Literal["query_metrics"] = "query_metrics"
    parameters: QueryMetricsParams

    def param_dict(self) -> dict:
        return self.parameters.model_dump()


class GetServiceStatusAction(Action):
    tool_name: Literal["get_service_status"] = "get_service_status"
    parameters: GetServiceStatusParams

    def param_dict(self) -> dict:
        return self.parameters.model_dump()


class GetDependencyMapAction(Action):
    tool_name: Literal["get_dependency_map"] = "get_dependency_map"
    parameters: GetDependencyMapParams

    def param_dict(self) -> dict:
        return self.parameters.model_dump()


class ConsultRunbookAction(Action):
    tool_name: Literal["consult_runbook"] = "consult_runbook"
    parameters: ConsultRunbookParams

    def param_dict(self) -> dict:
        return self.parameters.model_dump()


class CheckRecentChangesAction(Action):
    tool_name: Literal["check_recent_changes"] = "check_recent_changes"
    parameters: CheckRecentChangesParams

    def param_dict(self) -> dict:
        return self.parameters.model_dump()


class SubmitResolutionAction(Action):
    tool_name: Literal["submit_resolution"] = "submit_resolution"
    parameters: SubmitResolutionParams

    def param_dict(self) -> dict:
        return self.parameters.model_dump()


# ── Discriminated union ─────────────────────────────────────────────

_ActionUnion = Annotated[
    Union[
        QueryLogsAction,
        QueryMetricsAction,
        GetServiceStatusAction,
        GetDependencyMapAction,
        ConsultRunbookAction,
        CheckRecentChangesAction,
        SubmitResolutionAction,
    ],
    Field(discriminator="tool_name"),
]


class SentinelAction(RootModel[_ActionUnion]):
    """Discriminated union action — delegates to the matched concrete action."""

    @property
    def tool_name(self) -> str:
        return self.root.tool_name

    def param_dict(self) -> dict:
        return self.root.param_dict()


# ── Observation & State ─────────────────────────────────────────────


class SentinelObservation(Observation):
    """What the agent sees after each step."""

    incident_summary: str = Field(default="", description="Initial alert / ongoing context")
    tool_output: str = Field(default="", description="Result from the last tool call")
    available_tools: List[str] = Field(default_factory=list, description="Tools the agent can use")
    step_number: int = Field(default=0, description="Current step number")
    max_steps: int = Field(default=20, description="Maximum steps per episode")
    cumulative_reward: float = Field(default=0.0, description="Running total of per-step rewards")
    reward: Optional[float] = Field(default=None, description="Per-step reward for the last action")
    last_action_error: str = Field(default="", description="Error from last invalid action")
    tool_descriptions: dict = Field(default_factory=dict, description="Parameter metadata (populated on reset only)")


class SentinelState(State):
    """Internal environment state."""

    task_id: int = 1
    task_name: str = ""
    tools_called: List[str] = Field(default_factory=list)
    relevant_tools_called: List[str] = Field(default_factory=list)
    resolution_submitted: bool = False
    root_cause_correct: bool = False
    recommendation_correct: bool = False
    final_score: float = 1e-3
