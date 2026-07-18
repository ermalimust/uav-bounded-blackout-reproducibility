from __future__ import annotations

import math
import random
from dataclasses import replace
from pathlib import Path
from time import perf_counter
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.experiment_utils import markdown_table, write_csv
from uav_protocol_planning.models import IoTNode, ProtocolProfile, Scenario
from uav_protocol_planning.planners import (
    bounded_blackout_route,
    distance_only_route,
    protocol_aware_route,
)
from uav_protocol_planning.scenarios import build_random_scenario
from uav_protocol_planning.simulation import simulate_route


REPORT_DATE = "2026-07-18"
BUDGET_S = 90.0
SCENARIO_SEEDS = tuple(range(601, 651))
UNCERTAINTY_LEVELS = (0.0, 0.02, 0.05, 0.10)
PLANNERS = ("distance_only", "protocol_aware", "bounded_blackout")


def _jitter(value: float, rng: random.Random, level: float, floor: float = 0.0) -> float:
    return max(floor, value * rng.uniform(1.0 - level, 1.0 + level))


def _perturb_protocol(profile: ProtocolProfile, rng: random.Random, level: float) -> ProtocolProfile:
    packet_delta = rng.uniform(-0.08 * level, 0.12 * level)
    return replace(
        profile,
        data_rate_kbps=_jitter(profile.data_rate_kbps, rng, level, floor=0.01),
        connection_setup_s=_jitter(profile.connection_setup_s, rng, level, floor=0.0),
        reconnect_penalty_s=_jitter(profile.reconnect_penalty_s, rng, level, floor=0.0),
        packet_loss_at_edge=min(0.90, max(0.0, profile.packet_loss_at_edge + packet_delta)),
        switch_penalty_s=_jitter(profile.switch_penalty_s, rng, level, floor=0.0),
    )


def _perturb_node(node: IoTNode, protocols: dict[str, ProtocolProfile], rng: random.Random, level: float) -> IoTNode:
    cycle = protocols[node.protocol].sleep_cycle_s
    phase_jitter = rng.uniform(-level, level) * cycle
    return replace(
        node,
        first_awake_s=max(0.0, node.first_awake_s + phase_jitter),
        data_kb=_jitter(node.data_kb, rng, level, floor=0.01),
    )


def perturb_scenario(scenario: Scenario, seed: int, level: float) -> Scenario:
    rng = random.Random(seed)
    protocols = {
        name: _perturb_protocol(profile, rng, level)
        for name, profile in scenario.protocols.items()
    }
    nodes = {
        node_id: _perturb_node(node, protocols, rng, level)
        for node_id, node in scenario.nodes.items()
    }
    return replace(
        scenario,
        name=f"{scenario.name}_uncertainty_{level:.2f}",
        protocols=protocols,
        nodes=nodes,
    )


def _planned_route(planner: str, scenario):
    start = perf_counter()
    if planner == "distance_only":
        route = distance_only_route(scenario)
    elif planner == "protocol_aware":
        route = protocol_aware_route(scenario, blackout_weight=0.0)
    elif planner == "bounded_blackout":
        route = bounded_blackout_route(scenario, budget=BUDGET_S)
    else:
        raise ValueError(f"Unknown planner: {planner}")
    return route, (perf_counter() - start) * 1000.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _run_raw() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario_seed in SCENARIO_SEEDS:
        nominal = build_random_scenario(seed=scenario_seed, node_count=14)
        planned = {
            planner: _planned_route(planner, nominal)
            for planner in PLANNERS
        }
        for level in UNCERTAINTY_LEVELS:
            evaluated = perturb_scenario(nominal, seed=9000 + scenario_seed, level=level)
            for planner, (route, runtime_ms) in planned.items():
                result = simulate_route(evaluated, route)
                rows.append(
                    {
                        "scenario_seed": scenario_seed,
                        "uncertainty_level": level,
                        "planner": planner,
                        "total_time_s": round(result.total_time_s, 3),
                        "flight_distance_m": round(result.flight_distance_m, 3),
                        "max_blackout_s": round(result.max_blackout_s, 3),
                        "meets_90s_budget": int(result.max_blackout_s <= BUDGET_S + 1e-9),
                        "mission_feasible": int(result.mission_feasible),
                        "planning_runtime_ms": round(runtime_ms, 3),
                        "route": " -> ".join(route),
                    }
                )
        print(f"Finished uncertainty scenario seed={scenario_seed}")
    return rows


def _summarize(raw_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for level in UNCERTAINTY_LEVELS:
        level_rows = [row for row in raw_rows if abs(float(row["uncertainty_level"]) - level) <= 1e-12]
        for planner in PLANNERS:
            group = [row for row in level_rows if row["planner"] == planner]
            item: dict[str, object] = {
                "uncertainty_level": level,
                "planner": planner,
                "scenarios": len(group),
                "violations_90s": sum(1 - int(row["meets_90s_budget"]) for row in group),
                "endurance_violations": sum(1 - int(row["mission_feasible"]) for row in group),
            }
            for key in ("total_time_s", "flight_distance_m", "max_blackout_s", "planning_runtime_ms"):
                values = [float(row[key]) for row in group]
                item[f"{key}_mean"] = round(_mean(values), 3)
                item[f"{key}_std"] = round(_std(values), 3)
                item[f"{key}_ci95"] = round(1.96 * item[f"{key}_std"] / math.sqrt(len(values)), 3)
            summary.append(item)
    return summary


def _write_markdown(summary: list[dict[str, object]], path: Path) -> None:
    lines = [
        f"# Uncertainty Robustness - {REPORT_DATE}",
        "",
        "Routes are planned on the nominal scenario and evaluated after perturbing wake phase, data amount, protocol rate, setup/reconnect cost, switching cost, and edge loss.",
        "",
        *markdown_table(
            summary,
            [
                ("Uncertainty", "uncertainty_level"),
                ("Planner", "planner"),
                ("Scenarios", "scenarios"),
                ("Time mean", "total_time_s_mean"),
                ("Max blackout mean", "max_blackout_s_mean"),
                ("Max blackout 95% CI", "max_blackout_s_ci95"),
                ("90s violations", "violations_90s"),
                ("Endurance violations", "endurance_violations"),
                ("Planning runtime ms", "planning_runtime_ms_mean"),
            ],
        ),
        "",
        "Reading: the perturbation is a robustness check for known-profile offline planning, not an online replanning result.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    raw_rows = _run_raw()
    summary = _summarize(raw_rows)
    results_dir = ROOT / "results"
    write_csv(raw_rows, results_dir / f"uncertainty_robustness_raw_{REPORT_DATE}.csv")
    write_csv(summary, results_dir / f"uncertainty_robustness_summary_{REPORT_DATE}.csv")
    _write_markdown(summary, results_dir / f"uncertainty_robustness_{REPORT_DATE}.md")
    print("Wrote uncertainty robustness outputs.")


if __name__ == "__main__":
    main()
