from __future__ import annotations

from dataclasses import dataclass

from .models import SimulationResult


@dataclass(frozen=True)
class RouteTemporalMetrics:
    mean_communication_gap_s: float
    max_communication_gap_s: float
    average_silence_age_s: float
    mean_collection_completion_s: float


def route_temporal_metrics(result: SimulationResult) -> RouteTemporalMetrics:
    """Return average-style timing metrics for comparison with max blackout."""
    gaps = [float(event["communication_gap_s"]) for event in result.event_log]
    completions = [_event_completion_time_s(event) for event in result.event_log]

    if completions:
        return_gap_s = max(0.0, result.total_time_s - completions[-1])
        gaps.append(return_gap_s)
        mean_completion_s = sum(completions) / len(completions)
    else:
        gaps.append(result.total_time_s)
        mean_completion_s = result.total_time_s

    mean_gap_s = sum(gaps) / len(gaps)
    average_silence_age_s = sum((gap * gap) / 2.0 for gap in gaps) / max(
        result.total_time_s, 1e-9
    )

    return RouteTemporalMetrics(
        mean_communication_gap_s=mean_gap_s,
        max_communication_gap_s=result.max_blackout_s,
        average_silence_age_s=average_silence_age_s,
        mean_collection_completion_s=mean_completion_s,
    )


def _event_completion_time_s(event: dict[str, object]) -> float:
    if "completion_s" in event:
        return float(event["completion_s"])
    return (
        float(event["arrival_s"])
        + float(event["wait_s"])
        + float(event["setup_s"])
        + float(event["switch_s"])
        + float(event["transfer_s"])
    )
