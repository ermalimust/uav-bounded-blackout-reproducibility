from __future__ import annotations

import csv
from itertools import permutations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_protocol_planning.planners import (  # noqa: E402
    bounded_blackout_route,
    distance_only_route,
    genetic_algorithm_blackout_route,
    genetic_algorithm_route,
    ordinary_data_collection_route,
    particle_swarm_blackout_route,
    particle_swarm_route,
    protocol_aware_route,
)
from uav_protocol_planning.scenarios import build_random_scenario  # noqa: E402
from uav_protocol_planning.simulation import simulate_route  # noqa: E402


BUDGET_S = 90.0
REPORT_DATE = "2026-07-18"
NODE_COUNT = 8
SEEDS = tuple(range(201, 213))

PLANNER_ORDER = (
    "exact_bounded",
    "bounded_blackout",
    "protocol_aware",
    "genetic_algorithm",
    "particle_swarm",
    "ga_blackout",
    "pso_blackout",
    "distance_only",
    "ordinary_collection",
)


def _exact_bounded_route(scenario):
    best_min_blackout = None
    best_feasible = None
    for route in permutations(tuple(scenario.nodes)):
        result = simulate_route(scenario, route)
        min_key = (round(result.max_blackout_s, 9), round(result.total_time_s, 9))
        feasible_key = (round(result.total_time_s, 9), round(result.max_blackout_s, 9))
        if best_min_blackout is None or min_key < best_min_blackout[0]:
            best_min_blackout = (min_key, route, result)
        if result.max_blackout_s <= BUDGET_S + 1e-9 and result.mission_feasible:
            if best_feasible is None or feasible_key < best_feasible[0]:
                best_feasible = (feasible_key, route, result)

    if best_feasible is not None:
        return best_feasible[1], best_feasible[2], True
    assert best_min_blackout is not None
    return best_min_blackout[1], best_min_blackout[2], False


def _planner_routes(scenario):
    return {
        "distance_only": distance_only_route(scenario),
        "ordinary_collection": ordinary_data_collection_route(scenario),
        "protocol_aware": protocol_aware_route(scenario, blackout_weight=0.0),
        "bounded_blackout": bounded_blackout_route(scenario, BUDGET_S),
        "genetic_algorithm": genetic_algorithm_route(
            scenario,
            blackout_weight=3.0,
            population_size=20,
            generations=40,
        ),
        "particle_swarm": particle_swarm_route(
            scenario,
            blackout_weight=3.0,
            swarm_size=20,
            iterations=45,
        ),
        "ga_blackout": genetic_algorithm_blackout_route(
            scenario,
            population_size=20,
            generations=40,
        ),
        "pso_blackout": particle_swarm_blackout_route(
            scenario,
            swarm_size=20,
            iterations=45,
        ),
    }


def _write_csv(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _summarize(raw_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary = []
    exact_by_seed = {
        int(row["seed"]): row
        for row in raw_rows
        if row["planner"] == "exact_bounded"
    }
    scenario_count = len(exact_by_seed)

    for planner in PLANNER_ORDER:
        rows = [row for row in raw_rows if row["planner"] == planner]
        if not rows:
            continue
        violations = sum(
            float(row["max_blackout_s"]) > BUDGET_S + 1e-9
            or not bool(row["mission_feasible"])
            for row in rows
        )
        exact_matches = 0
        feasible_gaps = []
        blackout_gaps = []
        max_blackout_gap = None
        max_violation_over_budget = 0.0
        for row in rows:
            exact = exact_by_seed[int(row["seed"])]
            exact_match = (
                abs(float(row["total_time_s"]) - float(exact["total_time_s"])) <= 1e-6
                and abs(float(row["max_blackout_s"]) - float(exact["max_blackout_s"])) <= 1e-6
            )
            if exact_match:
                exact_matches += 1
            if (
                bool(row["meets_budget"])
                and bool(exact["meets_budget"])
                and bool(row["mission_feasible"])
                and bool(exact["mission_feasible"])
            ):
                feasible_gaps.append(
                    (float(row["total_time_s"]) - float(exact["total_time_s"]))
                    / max(1e-9, float(exact["total_time_s"]))
                    * 100.0
                )
            blackout_gap = float(row["max_blackout_s"]) - float(exact["max_blackout_s"])
            blackout_gaps.append(blackout_gap)
            max_blackout_gap = blackout_gap if max_blackout_gap is None else max(max_blackout_gap, blackout_gap)
            max_violation_over_budget = max(
                max_violation_over_budget,
                float(row["max_blackout_s"]) - BUDGET_S,
            )

        summary.append(
            {
                "planner": planner,
                "scenarios": scenario_count,
                "mean_time_s": round(sum(float(row["total_time_s"]) for row in rows) / len(rows), 3),
                "mean_max_blackout_s": round(sum(float(row["max_blackout_s"]) for row in rows) / len(rows), 3),
                "violations_over_90s": violations,
                "exact_matches": exact_matches,
                "mean_feasible_time_gap_pct": round(sum(feasible_gaps) / len(feasible_gaps), 3) if feasible_gaps else "",
                "mean_blackout_gap_s": round(sum(blackout_gaps) / len(blackout_gaps), 3),
                "max_blackout_gap_s": round(max_blackout_gap or 0.0, 3),
                "max_violation_over_budget_s": round(max(0.0, max_violation_over_budget), 3),
            }
        )

    return summary


def _write_markdown(summary_rows: list[dict[str, object]], path: Path) -> None:
    lines = [
        f"# Small Exact Benchmark - {REPORT_DATE}",
        "",
        f"Exhaustive enumeration over {len(SEEDS)} random {NODE_COUNT}-node scenarios with blackout budget beta = {BUDGET_S:g} s.",
        "",
        "| Planner | Time (s) | Max blackout (s) | Viol. | Exact matches | Feasible time gap (%) | Mean B gap (s) | Max B gap (s) | Max viol. (s) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            "| {planner} | {mean_time_s} | {mean_max_blackout_s} | {violations_over_90s} | {exact_matches} | {mean_feasible_time_gap_pct} | {mean_blackout_gap_s} | {max_blackout_gap_s} | {max_violation_over_budget_s} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "Notes:",
            "- `exact_bounded` is the fastest enumerated route satisfying both the 90 s blackout budget and mission endurance, or the minimum-blackout route if the joint constraints are infeasible.",
            "- `mean_feasible_time_gap_pct` is computed only on scenarios where both the planner and the exact route satisfy both constraints.",
            "- `mean_blackout_gap_s` is relative to the exact bounded solution in the same scenario.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    raw_rows: list[dict[str, object]] = []
    for index, seed in enumerate(SEEDS, start=1):
        scenario = build_random_scenario(seed=seed, node_count=NODE_COUNT)
        exact_route, exact_result, exact_feasible = _exact_bounded_route(scenario)
        raw_rows.append(
            {
                "seed": seed,
                "scenario": scenario.name,
                "planner": "exact_bounded",
                "total_time_s": round(exact_result.total_time_s, 6),
                "max_blackout_s": round(exact_result.max_blackout_s, 6),
                "meets_budget": exact_result.max_blackout_s <= BUDGET_S + 1e-9,
                "mission_feasible": exact_result.mission_feasible,
                "exact_budget_feasible": exact_feasible,
                "route": " -> ".join(exact_route),
            }
        )

        for planner, route in _planner_routes(scenario).items():
            result = simulate_route(scenario, route)
            raw_rows.append(
                {
                    "seed": seed,
                    "scenario": scenario.name,
                    "planner": planner,
                    "total_time_s": round(result.total_time_s, 6),
                    "max_blackout_s": round(result.max_blackout_s, 6),
                    "meets_budget": result.max_blackout_s <= BUDGET_S + 1e-9,
                    "mission_feasible": result.mission_feasible,
                    "exact_budget_feasible": exact_feasible,
                    "route": " -> ".join(route),
                }
            )
        print(f"Finished exact benchmark scenario {index}/{len(SEEDS)} (seed={seed})")

    summary_rows = _summarize(raw_rows)
    raw_path = ROOT / "results" / f"small_exact_benchmark_raw_{REPORT_DATE}.csv"
    summary_path = ROOT / "results" / f"small_exact_benchmark_summary_{REPORT_DATE}.csv"
    md_path = ROOT / "results" / f"small_exact_benchmark_{REPORT_DATE}.md"
    _write_csv(raw_rows, raw_path)
    _write_csv(summary_rows, summary_path)
    _write_markdown(summary_rows, md_path)
    print(f"Wrote {raw_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
