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
from uav_protocol_planning.metrics import route_temporal_metrics
from uav_protocol_planning.planners import (
    average_gap_route,
    blackout_focused_route,
    bounded_blackout_route,
    distance_only_route,
    freshness_focused_route,
    genetic_algorithm_route,
    ordinary_data_collection_route,
    particle_swarm_route,
    protocol_aware_route,
    soft_blackout_penalty_route,
)
from uav_protocol_planning.scenarios import (
    build_public_trace_calibrated_protocols,
    build_random_scenario,
)
from uav_protocol_planning.simulation import simulate_route


REPORT_DATE = "2026-07-04"
SCENARIO_SEEDS = tuple(range(101, 151))
PROFILE_VARIANT = "public_trace_calibrated"


CALIBRATION_NOTES = {
    "LoRa": (
        "Real-UAV LoRa/LoRaWAN public measurements for range, edge reliability, "
        "and aerial link variability; packet-capture LoRaWAN studies for "
        "low-rate and loss envelope."
    ),
    "ZigBee": (
        "Real-UAV 2.4 GHz IEEE 802.15.4 measurements for aerial edge loss and "
        "range collapse; XBee/802.15.4 studies for nominal rate and recovery."
    ),
    "BLE": (
        "Real-chipset BLE discovery/reconnect studies and RSSI-distance "
        "datasets; no public aerial BLE dataset was used."
    ),
    "WiFi": (
        "K10 Wi-Fi bench measurements for service-time scale plus conservative "
        "short-range edge-loss assumptions; no public aerial Wi-Fi IoT dataset "
        "was used."
    ),
}


CALIBRATION_STATUS = {
    "LoRa": "public real-UAV trace calibrated",
    "ZigBee": "public real-UAV trace calibrated",
    "BLE": "ground measurement / standard derived",
    "WiFi": "local bench / standard derived",
}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def protocol_profile_rows() -> list[dict[str, object]]:
    rows = []
    for profile in build_public_trace_calibrated_protocols().values():
        rows.append(
            {
                "protocol": profile.name,
                "range_m": profile.nominal_range_m,
                "rate_kbps": profile.data_rate_kbps,
                "setup_s": profile.connection_setup_s,
                "reconnect_s": profile.reconnect_penalty_s,
                "disconnect_threshold_s": profile.disconnect_threshold_s,
                "cycle_window_s": f"{profile.sleep_cycle_s:g}/{profile.awake_window_s:g}",
                "edge_loss": profile.packet_loss_at_edge,
                "switch_s": profile.switch_penalty_s,
                "calibration_status": CALIBRATION_STATUS[profile.name],
                "calibration_note": CALIBRATION_NOTES[profile.name],
            }
        )
    return rows


def _main_route_with_runtime(
    planner_name: str,
    scenario_seed: int,
    scenario,
) -> tuple[tuple[str, ...], float]:
    start = perf_counter()
    if planner_name == "distance_only":
        route = distance_only_route(scenario)
    elif planner_name == "ordinary_collection":
        route = ordinary_data_collection_route(scenario)
    elif planner_name == "protocol_aware":
        route = protocol_aware_route(scenario, blackout_weight=0.0)
    elif planner_name == "bounded_blackout":
        route = blackout_focused_route(scenario)
    elif planner_name == "genetic_algorithm":
        route = genetic_algorithm_route(
            scenario,
            blackout_weight=3.0,
            population_size=20,
            generations=40,
            seed=3000 + scenario_seed,
        )
    elif planner_name == "particle_swarm":
        route = particle_swarm_route(
            scenario,
            blackout_weight=3.0,
            swarm_size=20,
            iterations=45,
            seed=4000 + scenario_seed,
        )
    else:
        raise ValueError(f"Unknown planner: {planner_name}")
    return route, (perf_counter() - start) * 1000.0


def _metric_route_with_runtime(planner_name: str, scenario) -> tuple[tuple[str, ...], float]:
    start = perf_counter()
    if planner_name == "protocol_aware_time":
        route = protocol_aware_route(scenario, blackout_weight=0.0)
    elif planner_name == "soft_penalty_w12":
        route = soft_blackout_penalty_route(scenario, blackout_weight=12.0, budget=90.0)
    elif planner_name == "average_gap":
        route = average_gap_route(scenario, max_passes=12)
    elif planner_name == "freshness_focused":
        route = freshness_focused_route(scenario, max_passes=12)
    elif planner_name == "bounded_beta90":
        route = bounded_blackout_route(scenario, budget=90.0)
    else:
        raise ValueError(f"Unknown planner: {planner_name}")
    return route, (perf_counter() - start) * 1000.0


def _protocol_counts(scenario) -> dict[str, int]:
    counts = {name: 0 for name in scenario.protocols}
    for node in scenario.nodes.values():
        counts[node.protocol] = counts.get(node.protocol, 0) + 1
    return counts


def run_main_suite() -> list[dict[str, object]]:
    planners = (
        "distance_only",
        "ordinary_collection",
        "protocol_aware",
        "bounded_blackout",
        "genetic_algorithm",
        "particle_swarm",
    )
    rows: list[dict[str, object]] = []
    for scenario_seed in SCENARIO_SEEDS:
        scenario = build_random_scenario(
            seed=scenario_seed,
            node_count=14,
            profile_variant=PROFILE_VARIANT,
        )
        counts = _protocol_counts(scenario)
        for planner in planners:
            route, runtime_ms = _main_route_with_runtime(planner, scenario_seed, scenario)
            result = simulate_route(scenario, route)
            rows.append(
                {
                    "profile_variant": PROFILE_VARIANT,
                    "scenario": scenario.name,
                    "scenario_seed": scenario_seed,
                    "planner": planner,
                    "node_count": len(scenario.nodes),
                    "lora_nodes": counts.get("LoRa", 0),
                    "zigbee_nodes": counts.get("ZigBee", 0),
                    "ble_nodes": counts.get("BLE", 0),
                    "wifi_nodes": counts.get("WiFi", 0),
                    "total_time_s": round(result.total_time_s, 3),
                    "flight_distance_m": round(result.flight_distance_m, 3),
                    "max_blackout_s": round(result.max_blackout_s, 3),
                    "meets_90s_budget": int(result.max_blackout_s <= 90.0 + 1e-6),
                    "wait_time_s": round(result.wait_time_s, 3),
                    "service_time_s": round(result.service_time_s, 3),
                    "protocol_switches": result.protocol_switches,
                    "radio_obstacle_hits": result.radio_obstacle_hits,
                    "runtime_ms": round(runtime_ms, 3),
                    "route": " -> ".join(route),
                }
            )
    return rows


def run_metric_suite() -> list[dict[str, object]]:
    planners = (
        "protocol_aware_time",
        "soft_penalty_w12",
        "average_gap",
        "freshness_focused",
        "bounded_beta90",
    )
    rows: list[dict[str, object]] = []
    for scenario_seed in SCENARIO_SEEDS:
        scenario = build_random_scenario(
            seed=scenario_seed,
            node_count=14,
            profile_variant=PROFILE_VARIANT,
        )
        for planner in planners:
            route, runtime_ms = _metric_route_with_runtime(planner, scenario)
            result = simulate_route(scenario, route)
            temporal = route_temporal_metrics(result)
            rows.append(
                {
                    "profile_variant": PROFILE_VARIANT,
                    "scenario": scenario.name,
                    "scenario_seed": scenario_seed,
                    "planner": planner,
                    "total_time_s": round(result.total_time_s, 3),
                    "max_blackout_s": round(result.max_blackout_s, 3),
                    "mean_gap_s": round(temporal.mean_communication_gap_s, 3),
                    "average_silence_age_s": round(temporal.average_silence_age_s, 3),
                    "mean_collection_completion_s": round(
                        temporal.mean_collection_completion_s, 3
                    ),
                    "meets_90s_budget": int(result.max_blackout_s <= 90.0 + 1e-6),
                    "runtime_ms": round(runtime_ms, 3),
                    "route": " -> ".join(route),
                }
            )
    return rows


def summarize(rows: list[dict[str, object]], keys: tuple[str, ...]) -> list[dict[str, object]]:
    planners = sorted({str(row["planner"]) for row in rows})
    summary = []
    for planner in planners:
        group = [row for row in rows if row["planner"] == planner]
        item: dict[str, object] = {
            "profile_variant": PROFILE_VARIANT,
            "planner": planner,
            "scenarios": len(group),
        }
        if "meets_90s_budget" in group[0]:
            item["budget_violations"] = sum(
                1 - int(row["meets_90s_budget"]) for row in group
            )
        for key in keys:
            values = [float(row[key]) for row in group]
            item[f"{key}_mean"] = round(_mean(values), 3)
            item[f"{key}_std"] = round(_std(values), 3)
            item[f"{key}_ci95"] = round(1.96 * item[f"{key}_std"] / math.sqrt(len(values)), 3)
        summary.append(item)
    return summary


def write_markdown(
    profile_rows: list[dict[str, object]],
    main_summary: list[dict[str, object]],
    metric_summary: list[dict[str, object]],
    path: Path,
) -> None:
    lines = [
        f"# Public measurement-trace calibrated profile rerun - {REPORT_DATE}",
        "",
        "This check keeps the scenario generator, node count, seeds, and routers fixed, but replaces the reference protocol profile with a public measurement-trace calibrated profile. It is not a closed-loop UAV deployment experiment. Public real-UAV traces are used for the LoRa and ZigBee-class radio envelope; BLE and WiFi fields remain grounded in ground/bench measurements and standards.",
        "",
        "## Calibrated protocol profile",
        "",
        *markdown_table(
            profile_rows,
            [
                ("Protocol", "protocol"),
                ("Range", "range_m"),
                ("Rate", "rate_kbps"),
                ("Setup", "setup_s"),
                ("Reconnect", "reconnect_s"),
                ("Disc.", "disconnect_threshold_s"),
                ("Cycle/window", "cycle_window_s"),
                ("Edge loss", "edge_loss"),
                ("Status", "calibration_status"),
            ],
        ),
        "",
        "## Calibration notes",
        "",
    ]
    for row in profile_rows:
        lines.append(f"- {row['protocol']}: {row['calibration_note']}")
    lines.extend(
        [
            "",
            "## Main random-suite summary",
            "",
            *markdown_table(
                main_summary,
                [
                    ("Planner", "planner"),
                    ("Scenarios", "scenarios"),
                    ("Time mean", "total_time_s_mean"),
                    ("Max blackout mean", "max_blackout_s_mean"),
                    ("Max blackout std", "max_blackout_s_std"),
                    ("90s violations", "budget_violations"),
                    ("Runtime mean ms", "runtime_ms_mean"),
                ],
            ),
            "",
            "## Average/freshness-style checks",
            "",
            *markdown_table(
                metric_summary,
                [
                    ("Planner", "planner"),
                    ("Scenarios", "scenarios"),
                    ("Time mean", "total_time_s_mean"),
                    ("Max blackout mean", "max_blackout_s_mean"),
                    ("Mean gap mean", "mean_gap_s_mean"),
                    ("Mean completion mean", "mean_collection_completion_s_mean"),
                    ("90s violations", "budget_violations"),
                ],
            ),
            "",
            "Reading: this check should be interpreted as public measurement-trace calibration of scheduler inputs, not as closed-loop real-UAV validation of the route controller.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    results_dir = ROOT / "results"
    profile_rows = protocol_profile_rows()
    main_rows = run_main_suite()
    metric_rows = run_metric_suite()
    main_summary = summarize(
        main_rows,
        (
            "total_time_s",
            "flight_distance_m",
            "max_blackout_s",
            "wait_time_s",
            "service_time_s",
            "protocol_switches",
            "radio_obstacle_hits",
            "runtime_ms",
        ),
    )
    metric_summary = summarize(
        metric_rows,
        (
            "total_time_s",
            "max_blackout_s",
            "mean_gap_s",
            "average_silence_age_s",
            "mean_collection_completion_s",
            "runtime_ms",
        ),
    )

    write_csv(
        profile_rows,
        results_dir / f"public_trace_profile_table_{REPORT_DATE}.csv",
    )
    write_csv(
        main_rows,
        results_dir / f"public_trace_multiscenario_raw_{REPORT_DATE}.csv",
    )
    write_csv(
        main_summary,
        results_dir / f"public_trace_multiscenario_summary_{REPORT_DATE}.csv",
    )
    write_csv(
        metric_rows,
        results_dir / f"public_trace_metric_checks_raw_{REPORT_DATE}.csv",
    )
    write_csv(
        metric_summary,
        results_dir / f"public_trace_metric_checks_summary_{REPORT_DATE}.csv",
    )
    write_markdown(
        profile_rows,
        main_summary,
        metric_summary,
        results_dir / f"public_trace_calibration_{REPORT_DATE}.md",
    )

    print(f"Wrote public measurement-trace calibration outputs for {REPORT_DATE}.")


if __name__ == "__main__":
    main()
