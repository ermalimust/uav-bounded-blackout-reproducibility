from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from uav_protocol_planning.models import Scenario
from uav_protocol_planning.planners import (
    bounded_blackout_route,
    distance_only_route,
    genetic_algorithm_route,
    ordinary_data_collection_route,
    particle_swarm_route,
    protocol_aware_route,
)
from uav_protocol_planning.simulation import simulate_route


def planner_routes(
    scenario: Scenario,
    ga_population_size: int = 32,
    ga_generations: int = 70,
    pso_swarm_size: int = 28,
    pso_iterations: int = 80,
    blackout_budget_s: float = 90.0,
) -> dict[str, tuple[str, ...]]:
    return {
        "distance_only": distance_only_route(scenario),
        "ordinary_collection": ordinary_data_collection_route(scenario),
        "protocol_aware": protocol_aware_route(scenario, blackout_weight=0.0),
        "bounded_blackout": bounded_blackout_route(
            scenario,
            budget=blackout_budget_s,
        ),
        "genetic_algorithm": genetic_algorithm_route(
            scenario,
            blackout_weight=3.0,
            population_size=ga_population_size,
            generations=ga_generations,
        ),
        "particle_swarm": particle_swarm_route(
            scenario,
            blackout_weight=3.0,
            swarm_size=pso_swarm_size,
            iterations=pso_iterations,
        ),
    }


def planner_rows(
    label: str,
    scenario: Scenario,
    extra: dict[str, object] | None = None,
    ga_population_size: int = 32,
    ga_generations: int = 70,
    pso_swarm_size: int = 28,
    pso_iterations: int = 80,
    blackout_budget_s: float = 90.0,
) -> list[dict[str, object]]:
    rows = []
    for planner, route in planner_routes(
        scenario,
        ga_population_size,
        ga_generations,
        pso_swarm_size,
        pso_iterations,
        blackout_budget_s,
    ).items():
        result = simulate_route(scenario, route)
        row = {
            "scenario": label,
            "planner": planner,
            "total_time_s": round(result.total_time_s, 3),
            "flight_distance_m": round(result.flight_distance_m, 3),
            "success_rate": round(result.data_success_rate, 3),
            "mission_feasible": result.mission_feasible,
            "max_blackout_s": round(result.max_blackout_s, 3),
            "wait_time_s": round(result.wait_time_s, 3),
            "service_time_s": round(result.service_time_s, 3),
            "reconnect_count": result.reconnect_count,
            "protocol_switches": result.protocol_switches,
            "radio_obstacle_hits": result.radio_obstacle_hits,
            "route": " -> ".join(result.route),
        }
        if extra:
            row.update(extra)
        rows.append(row)
    return rows


def write_csv(rows: Iterable[dict[str, object]], path: Path) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> list[str]:
    headers = [header for header, _ in columns]
    keys = [key for _, key in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[key]) for key in keys) + " |")
    return lines
