"""Per-step reward calculator."""

from dataclasses import dataclass, field
from typing import List

from tools.registry import make_relevance_key

REWARD_RELEVANT = 0.12
REWARD_IRRELEVANT = -0.02
REWARD_REPEATED = -0.05
REWARD_INVALID = -0.03
REWARD_STEP_COST = -0.01


@dataclass
class RewardComponent:
    label: str
    value: float


@dataclass
class RewardBreakdown:
    components: List[RewardComponent] = field(default_factory=list)
    classification: str = ""
    reason: str = ""


def _call_signature(tool_name: str, params: dict) -> str:
    """Create a hashable signature for a tool call to detect repeats."""
    return make_relevance_key(tool_name, params)


def _is_relevant(
    tool_name: str,
    params: dict,
    relevant_tools: List[str],
) -> bool:
    """Check if a tool call matches the scenario's relevance list.

    Each entry is a colon-joined string like "query_logs:auth-service".
    A match requires the computed key to appear in the relevance list.
    """
    key = make_relevance_key(tool_name, params)
    return key in relevant_tools


def compute_step_reward(
    tool_name: str,
    params: dict,
    is_valid: bool,
    relevant_tools: List[str],
    previous_calls: List[str],
) -> tuple[float, RewardBreakdown]:
    """Compute the reward for a single step.

    Returns (reward, breakdown).  Caller is responsible for appending the call
    signature to previous_calls after calling this.
    """
    step_cost = RewardComponent("step_cost", REWARD_STEP_COST)

    if not is_valid:
        invalid_component = RewardComponent("invalid", REWARD_INVALID)
        reward = REWARD_STEP_COST + REWARD_INVALID
        breakdown = RewardBreakdown(
            components=[step_cost, invalid_component],
            classification="invalid",
            reason=f"invalid action: {REWARD_INVALID:+.2f}, step cost: {REWARD_STEP_COST:+.2f}",
        )
        return reward, breakdown

    sig = _call_signature(tool_name, params)
    if sig in previous_calls:
        repeated_component = RewardComponent("repeated", REWARD_REPEATED)
        reward = REWARD_STEP_COST + REWARD_REPEATED
        breakdown = RewardBreakdown(
            components=[step_cost, repeated_component],
            classification="repeated",
            reason=f"repeated tool call ({sig}): {REWARD_REPEATED:+.2f}, step cost: {REWARD_STEP_COST:+.2f}",
        )
        return reward, breakdown

    if _is_relevant(tool_name, params, relevant_tools):
        relevant_component = RewardComponent("relevant", REWARD_RELEVANT)
        reward = REWARD_STEP_COST + REWARD_RELEVANT
        breakdown = RewardBreakdown(
            components=[step_cost, relevant_component],
            classification="relevant",
            reason=f"relevant tool call ({sig}): {REWARD_RELEVANT:+.2f}, step cost: {REWARD_STEP_COST:+.2f}",
        )
    else:
        irrelevant_component = RewardComponent("irrelevant", REWARD_IRRELEVANT)
        reward = REWARD_STEP_COST + REWARD_IRRELEVANT
        breakdown = RewardBreakdown(
            components=[step_cost, irrelevant_component],
            classification="irrelevant",
            reason=f"irrelevant tool call ({sig}): {REWARD_IRRELEVANT:+.2f}, step cost: {REWARD_STEP_COST:+.2f}",
        )

    return reward, breakdown
