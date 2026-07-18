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
from uav_protocol_planning.models import IoTNode, Scenario
from uav_protocol_planning.planners import (
    bounded_blackout_route,
    distance_only_route,
    protocol_aware_route,
)
from uav_protocol_planning.scenarios import build_random_scenario
from uav_protocol_planning.simulation import simulate_route


REPORT_DATE = "2026-07-18"
BUDGET_S = 90.0
SCENARIO_SEEDS = tuple(range(701, 751))
PHASE_ERROR_S = (0.0, 2.0, 5.0, 10.0, 20.0, 30.0)
PLANNERS = ("distance_only", "protocol_aware", "bounded_blackout")


def _shift_node_phase(node: IoTNode, scenario: Scenario, rng: random.Random, delta_s: float) -> IoTNode:
    protocol = scenario.protocols[node.protocol]
    if protocol.sleep_cycle_s <= 0:
        return node
    shifted = node.first_awake_s + rng.uniform(-delta_s, delta_s)
    return replace(node, first_awake_s=shifted % protocol.sleep_cycle_s)


def phase_perturbed_scenario(scenario: Scenario, seed: int, delta_s: float) -> Scenario:
    rng = random.Random(seed)
    nodes = {
        node_id: _shift_node_phase(node, scenario, rng, delta_s)
        for node_id, node in scenario.nodes.items()
    }
    return replace(
        scenario,
        name=f"{scenario.name}_phase_error_{delta_s:g}s",
        nodes=nodes,
    )


def _planned_route(planner: str, scenario: Scenario) -> tuple[tuple[str, ...], float]:
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
        for delta_s in PHASE_ERROR_S:
            evaluated = phase_perturbed_scenario(
                nominal,
                seed=12000 + scenario_seed + int(delta_s * 10),
                delta_s=delta_s,
            )
            for planner, (route, runtime_ms) in planned.items():
                result = simulate_route(evaluated, route)
                rows.append(
                    {
                        "scenario_seed": scenario_seed,
                        "phase_error_s": delta_s,
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
        print(f"Finished phase perturbation scenario seed={scenario_seed}")
    return rows


def _summarize(raw_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for delta_s in PHASE_ERROR_S:
        delta_rows = [
            row for row in raw_rows
            if abs(float(row["phase_error_s"]) - delta_s) <= 1e-12
        ]
        for planner in PLANNERS:
            group = [row for row in delta_rows if row["planner"] == planner]
            item: dict[str, object] = {
                "phase_error_s": delta_s,
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
        f"# Wake-Phase Perturbation Study - {REPORT_DATE}",
        "",
        "Routes are planned on nominal wake phases and evaluated after shifting each node phase by a uniformly sampled error in [-Delta, Delta]. Only wake phase is perturbed; protocol rates, setup/reconnect costs, packet loss, and data amounts remain nominal.",
        "",
        *markdown_table(
            summary,
            [
                ("Delta (s)", "phase_error_s"),
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
        "Reading: this isolates the reviewer-requested phase-error effect. It does not claim online replanning; it bounds the known-profile assumption under offline planning.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    raw_rows = _run_raw()
    summary = _summarize(raw_rows)
    results_dir = ROOT / "results"
    write_csv(raw_rows, results_dir / f"phase_perturbation_raw_{REPORT_DATE}.csv")
    write_csv(summary, results_dir / f"phase_perturbation_summary_{REPORT_DATE}.csv")
    _write_markdown(summary, results_dir / f"phase_perturbation_{REPORT_DATE}.md")
    print("Wrote wake-phase perturbation outputs.")


if __name__ == "__main__":
    main()
