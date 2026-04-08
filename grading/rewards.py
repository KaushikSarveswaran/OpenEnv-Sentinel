"""Per-step reward calculator."""

from typing import List

from tools.registry import make_relevance_key

REWARD_RELEVANT = 0.12
REWARD_IRRELEVANT = -0.02
REWARD_REPEATED = -0.05
REWARD_INVALID = -0.03
REWARD_STEP_COST = -0.01


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
) -> float:
    """Compute the reward for a single step.

    Returns the reward value.  Caller is responsible for appending the call
    signature to previous_calls after calling this.
    """
    reward = REWARD_STEP_COST

    if not is_valid:
        reward += REWARD_INVALID
        return reward

    sig = _call_signature(tool_name, params)
    if sig in previous_calls:
        reward += REWARD_REPEATED
        return reward

    if _is_relevant(tool_name, params, relevant_tools):
        reward += REWARD_RELEVANT
    else:
        reward += REWARD_IRRELEVANT

    return reward
