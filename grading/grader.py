"""Terminal grader — delegates to the scenario's grade_resolution method."""


def normalize_service_name(name: str) -> str:
    """Normalize an affected_service string for comparison."""
    return name.lower().strip().replace("_", "-")


def grade(scenario, resolution: dict, step_count: int) -> dict:
    """Grade a resolution using the scenario's grading logic.

    Returns dict with keys: score (float 0-1), root_cause_correct (bool),
    recommendation_correct (bool).
    """
    return scenario.grade_resolution(resolution, step_count)
