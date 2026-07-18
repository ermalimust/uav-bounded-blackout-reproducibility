from __future__ import annotations

import csv
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
from uav_protocol_planning.metrics import route_temporal_metrics
from uav_protocol_planning.planners import (
    average_gap_route,
    bounded_blackout_route,
    distance_only_route,
    freshness_focused_route,
    ordinary_data_collection_route,
    protocol_aware_route,
    soft_blackout_penalty_route,
)
from uav_protocol_planning.scenarios import build_random_scenario, build_reference_scenario
from uav_protocol_planning.simulation import simulate_route


REPORT_DATE = "2026-07-18"
SCENARIO_SEEDS = tuple(range(101, 151))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _is_success(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def summarize_k10_logs() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    files = sorted(ROOT.glob("experiments/k10_latency_log_*.csv"))
    files.extend(sorted(ROOT.glob("experiments/k10_distance_test_*_raw.csv")))

    all_times: list[float] = []
    all_success = 0
    all_requests = 0

    for path in files:
        records = _read_csv(path)
        times = [
            float(row["response_time_ms"])
            for row in records
            if row.get("response_time_ms", "") not in {"", None}
        ]
        successes = sum(1 for row in records if _is_success(row.get("success")))
        requests = len(records)
        all_times.extend(times)
        all_success += successes
        all_requests += requests
        rows.append(
            {
                "source": path.name,
                "requests": requests,
                "successes": successes,
                "success_rate_percent": round(100.0 * successes / requests, 1) if requests else 0.0,
                "mean_latency_ms": round(_mean(times), 1) if times else "",
                "min_latency_ms": round(min(times), 1) if times else "",
                "max_latency_ms": round(max(times), 1) if times else "",
            }
        )

    if all_requests:
        rows.append(
            {
                "source": "combined_k10_wifi_http",
                "requests": all_requests,
                "successes": all_success,
                "success_rate_percent": round(100.0 * all_success / all_requests, 1),
                "mean_latency_ms": round(_mean(all_times), 1),
                "min_latency_ms": round(min(all_times), 1),
                "max_latency_ms": round(max(all_times), 1),
            }
        )
    return rows


def _route_with_runtime(planner: str, scenario) -> tuple[tuple[str, ...], float]:
    start = perf_counter()
    if planner == "distance_only":
        route = distance_only_route(scenario)
    elif planner == "ordinary_collection":
        route = ordinary_data_collection_route(scenario)
    elif planner == "protocol_aware_time":
        route = protocol_aware_route(scenario, blackout_weight=0.0)
    elif planner == "soft_penalty_w12":
        route = soft_blackout_penalty_route(scenario, blackout_weight=12.0, budget=90.0)
    elif planner == "average_gap":
        route = average_gap_route(scenario, max_passes=12)
    elif planner == "freshness_focused":
        route = freshness_focused_route(scenario, max_passes=12)
    elif planner == "bounded_beta90":
        route = bounded_blackout_route(scenario, budget=90.0)
    else:
        raise ValueError(f"Unknown planner: {planner}")
    return route, (perf_counter() - start) * 1000.0


def run_baseline_checks() -> list[dict[str, object]]:
    planners = (
        "distance_only",
        "ordinary_collection",
        "protocol_aware_time",
        "soft_penalty_w12",
        "average_gap",
        "freshness_focused",
        "bounded_beta90",
    )
    rows: list[dict[str, object]] = []
    scenarios = [("reference", build_reference_scenario())]
    scenarios.extend(
        (f"random_{seed}", build_random_scenario(seed=seed, node_count=14))
        for seed in SCENARIO_SEEDS
    )

    for scenario_label, scenario in scenarios:
        for planner in planners:
            route, runtime_ms = _route_with_runtime(planner, scenario)
            result = simulate_route(scenario, route)
            temporal = route_temporal_metrics(result)
            rows.append(
                {
                    "scenario": scenario_label,
                    "planner": planner,
                    "total_time_s": round(result.total_time_s, 3),
                    "max_blackout_s": round(result.max_blackout_s, 3),
                    "mean_gap_s": round(temporal.mean_communication_gap_s, 3),
                    "average_silence_age_s": round(temporal.average_silence_age_s, 3),
                    "mean_collection_completion_s": round(
                        temporal.mean_collection_completion_s, 3
                    ),
                    "meets_90s_budget": int(result.max_blackout_s <= 90.0 + 1e-6),
                    "mission_feasible": int(result.mission_feasible),
                    "runtime_ms": round(runtime_ms, 3),
                    "route": " -> ".join(route),
                }
            )
    return rows


def summarize_baselines(raw_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary = []
    random_rows = [row for row in raw_rows if str(row["scenario"]).startswith("random_")]
    for planner in dict.fromkeys(row["planner"] for row in random_rows):
        group = [row for row in random_rows if row["planner"] == planner]
        item: dict[str, object] = {
            "planner": planner,
            "scenarios": len(group),
            "budget_violations": sum(1 - int(row["meets_90s_budget"]) for row in group),
            "endurance_violations": sum(1 - int(row["mission_feasible"]) for row in group),
            "joint_violations": sum(
                not int(row["meets_90s_budget"]) or not int(row["mission_feasible"])
                for row in group
            ),
        }
        for key in (
            "total_time_s",
            "max_blackout_s",
            "mean_gap_s",
            "average_silence_age_s",
            "mean_collection_completion_s",
            "runtime_ms",
        ):
            values = [float(row[key]) for row in group]
            item[f"{key}_mean"] = round(_mean(values), 3)
            item[f"{key}_std"] = round(_std(values), 3)
        summary.append(item)
    return summary


def write_markdown(
    k10_rows: list[dict[str, object]],
    baseline_summary: list[dict[str, object]],
    path: Path,
) -> None:
    lines = [
        f"# Task-driven gap checks - {REPORT_DATE}",
        "",
        "These checks add three reviewer-facing pieces of evidence: a small K10 WiFi reality check, a fixed soft-blackout-penalty baseline, and average/freshness-style metric baselines.",
        "",
        "## 1. K10 WiFi sanity evidence",
        "",
        *markdown_table(
            k10_rows,
            [
                ("Source", "source"),
                ("Requests", "requests"),
                ("Successes", "successes"),
                ("Success rate (%)", "success_rate_percent"),
                ("Mean latency (ms)", "mean_latency_ms"),
                ("Min latency (ms)", "min_latency_ms"),
                ("Max latency (ms)", "max_latency_ms"),
            ],
        ),
        "",
        "Interpretation: these logs only support a minimal WiFi sanity check for K10-as-node operation. They do not yet measure RSSI, distance curves, BLE/LoRa, or true reconnect delay.",
        "",
        "## 2. Soft penalty and average/freshness baselines",
        "",
        f"Random-suite summary over {len(SCENARIO_SEEDS)} heterogeneous scenarios. The budget column counts how often a route exceeds a 90 s maximum-blackout target.",
        "",
        *markdown_table(
            baseline_summary,
            [
                ("Planner", "planner"),
                ("Scenarios", "scenarios"),
                ("Time mean", "total_time_s_mean"),
                ("Max blackout mean", "max_blackout_s_mean"),
                ("Mean gap mean", "mean_gap_s_mean"),
                ("Mean completion mean", "mean_collection_completion_s_mean"),
                ("90s violations", "budget_violations"),
                ("Endurance violations", "endurance_violations"),
                ("Joint violations", "joint_violations"),
                ("Runtime ms", "runtime_ms_mean"),
            ],
        ),
        "",
        "Interpretation: the fixed soft penalty and averaged timing objectives are useful comparators, but they do not expose a hard operating guarantee. The constrained bounded-blackout router is the only baseline here that directly targets a specified maximum-blackout budget.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    results_dir = ROOT / "results"
    k10_rows = summarize_k10_logs()
    raw_rows = run_baseline_checks()
    summary_rows = summarize_baselines(raw_rows)

    write_csv(k10_rows, results_dir / f"k10_reality_check_summary_{REPORT_DATE}.csv")
    write_csv(raw_rows, results_dir / f"task_driven_gap_checks_raw_{REPORT_DATE}.csv")
    write_csv(summary_rows, results_dir / f"task_driven_gap_checks_summary_{REPORT_DATE}.csv")
    write_markdown(
        k10_rows,
        summary_rows,
        results_dir / f"task_driven_gap_checks_{REPORT_DATE}.md",
    )

    print(f"Wrote task-driven gap-check outputs for {REPORT_DATE}.")


if __name__ == "__main__":
    main()
