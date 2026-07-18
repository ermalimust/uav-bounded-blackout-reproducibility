from __future__ import annotations

import math
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
from uav_protocol_planning.planners import (
    bounded_blackout_route,
    distance_only_route,
    protocol_aware_route,
)
from uav_protocol_planning.scenarios import build_random_scenario
from uav_protocol_planning.simulation import simulate_route


REPORT_DATE = "2026-07-18"
BUDGET_S = 90.0
NODE_COUNTS = (25, 50, 100, 200)
SEEDS = (501, 502, 503)
PLANNERS = ("distance_only", "protocol_aware", "bounded_blackout")
MODES = {
    "seed_only": 0,
    "capped_6_passes": 6,
}
CAPPED_LOCAL_SEARCH_NODE_COUNTS = (25, 50)


def _route_with_runtime(planner: str, scenario, search_passes: int | None):
    start = perf_counter()
    if planner == "distance_only":
        route = distance_only_route(scenario)
    elif planner == "protocol_aware":
        if search_passes is None:
            route = protocol_aware_route(scenario, blackout_weight=0.0)
        else:
            route = protocol_aware_route(
                scenario,
                blackout_weight=0.0,
                max_passes=search_passes,
            )
    elif planner == "bounded_blackout":
        if search_passes is None:
            route = bounded_blackout_route(scenario, budget=BUDGET_S)
        else:
            route = bounded_blackout_route(
                scenario,
                budget=BUDGET_S,
                blackout_passes=search_passes,
                seed_max_passes=search_passes,
            )
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
    for mode, search_passes in MODES.items():
        node_counts = NODE_COUNTS if mode == "seed_only" else CAPPED_LOCAL_SEARCH_NODE_COUNTS
        for node_count in node_counts:
            for seed in SEEDS:
                scenario = build_random_scenario(seed=seed, node_count=node_count)
                for planner in PLANNERS:
                    route, runtime_ms = _route_with_runtime(planner, scenario, search_passes)
                    result = simulate_route(scenario, route)
                    rows.append(
                        {
                            "search_mode": mode,
                            "node_count": node_count,
                            "seed": seed,
                            "scenario": scenario.name,
                            "planner": planner,
                            "total_time_s": round(result.total_time_s, 3),
                            "flight_distance_m": round(result.flight_distance_m, 3),
                            "max_blackout_s": round(result.max_blackout_s, 3),
                            "meets_90s_budget": int(result.max_blackout_s <= BUDGET_S + 1e-9),
                            "mission_feasible": int(result.mission_feasible),
                            "runtime_ms": round(runtime_ms, 3),
                            "route": " -> ".join(route),
                        }
                    )
                print(f"Finished scalability mode={mode}, n={node_count}, seed={seed}")
    return rows


def _summarize(raw_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for mode in MODES:
        mode_rows = [row for row in raw_rows if row["search_mode"] == mode]
        for node_count in sorted({int(row["node_count"]) for row in mode_rows}):
            count_rows = [row for row in mode_rows if int(row["node_count"]) == node_count]
            for planner in PLANNERS:
                group = [row for row in count_rows if row["planner"] == planner]
                item: dict[str, object] = {
                    "search_mode": mode,
                    "node_count": node_count,
                    "planner": planner,
                    "scenarios": len(group),
                    "violations_90s": sum(1 - int(row["meets_90s_budget"]) for row in group),
                    "endurance_violations": sum(1 - int(row["mission_feasible"]) for row in group),
                }
                for key in ("total_time_s", "flight_distance_m", "max_blackout_s", "runtime_ms"):
                    values = [float(row[key]) for row in group]
                    item[f"{key}_mean"] = round(_mean(values), 3)
                    item[f"{key}_std"] = round(_std(values), 3)
                summary.append(item)
    return summary


def _write_markdown(summary: list[dict[str, object]], path: Path) -> None:
    lines = [
        f"# Scalability Study - {REPORT_DATE}",
        "",
        f"Each row averages {len(SEEDS)} random heterogeneous scenario(s). The budget is {BUDGET_S:g} s.",
        "`seed_only` uses no local-search passes and isolates large-n runtime of the seed/candidate-pool construction; `capped_6_passes` uses six deterministic first-improvement passes and is reported for 25 and 50 nodes.",
        "",
        *markdown_table(
            summary,
            [
                ("Mode", "search_mode"),
                ("Nodes", "node_count"),
                ("Planner", "planner"),
                ("Scenarios", "scenarios"),
                ("Time mean", "total_time_s_mean"),
                ("Distance mean", "flight_distance_m_mean"),
                ("Max blackout mean", "max_blackout_s_mean"),
                ("90s violations", "violations_90s"),
                ("Endurance violations", "endurance_violations"),
                ("Runtime mean ms", "runtime_ms_mean"),
            ],
        ),
        "",
        "Reading: this is an implementation-level scaling check, not a hardware-independent complexity claim.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    raw_rows = _run_raw()
    summary = _summarize(raw_rows)
    results_dir = ROOT / "results"
    write_csv(raw_rows, results_dir / f"scalability_raw_{REPORT_DATE}.csv")
    write_csv(summary, results_dir / f"scalability_summary_{REPORT_DATE}.csv")
    _write_markdown(summary, results_dir / f"scalability_{REPORT_DATE}.md")
    print("Wrote scalability outputs.")


if __name__ == "__main__":
    main()
