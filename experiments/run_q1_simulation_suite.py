from __future__ import annotations

import math
import csv
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
    action_masked_ppo_route,
    bounded_blackout_route,
    distance_only_route,
    genetic_algorithm_blackout_route,
    genetic_algorithm_route,
    neural_q_blackout_route,
    ordinary_data_collection_route,
    particle_swarm_blackout_route,
    particle_swarm_route,
    protocol_aware_route,
    q_learning_blackout_route,
)
from uav_protocol_planning.scenarios import build_random_scenario
from uav_protocol_planning.simulation import simulate_route


REPORT_DATE = "2026-07-18"
SCENARIO_SEEDS = tuple(range(101, 151))


def _route_with_runtime(planner_name: str, scenario_seed: int, scenario) -> tuple[tuple[str, ...], float]:
    start = perf_counter()
    if planner_name == "distance_only":
        route = distance_only_route(scenario)
    elif planner_name == "ordinary_collection":
        route = ordinary_data_collection_route(scenario)
    elif planner_name == "protocol_aware":
        route = protocol_aware_route(scenario, blackout_weight=0.0)
    elif planner_name == "bounded_blackout":
        route = bounded_blackout_route(scenario, budget=90.0)
    elif planner_name == "genetic_algorithm":
        route = genetic_algorithm_route(
            scenario,
            blackout_weight=3.0,
            population_size=20,
            generations=40,
            seed=1000 + scenario_seed,
        )
    elif planner_name == "particle_swarm":
        route = particle_swarm_route(
            scenario,
            blackout_weight=3.0,
            swarm_size=20,
            iterations=45,
            seed=2000 + scenario_seed,
        )
    elif planner_name == "ga_blackout":
        route = genetic_algorithm_blackout_route(
            scenario,
            population_size=20,
            generations=40,
            seed=3000 + scenario_seed,
        )
    elif planner_name == "pso_blackout":
        route = particle_swarm_blackout_route(
            scenario,
            swarm_size=20,
            iterations=45,
            seed=4000 + scenario_seed,
        )
    elif planner_name == "q_learning_blackout":
        route = q_learning_blackout_route(
            scenario,
            budget=90.0,
            episodes=320,
            seed=5000 + scenario_seed,
            repair_passes=8,
        )
    elif planner_name == "neural_q_blackout":
        route = neural_q_blackout_route(
            scenario,
            budget=90.0,
            episodes=220,
            hidden_size=24,
            batch_size=16,
            seed=6000 + scenario_seed,
            repair_passes=12,
        )
    elif planner_name == "am_ppo":
        route = action_masked_ppo_route(
            scenario,
            budget=90.0,
            episodes=360,
            hidden_size=24,
            update_epochs=3,
            seed=7000 + scenario_seed,
            repair_passes=0,
        )
    elif planner_name == "am_ppo_plus_ls":
        route = action_masked_ppo_route(
            scenario,
            budget=90.0,
            episodes=360,
            hidden_size=24,
            update_epochs=3,
            seed=7000 + scenario_seed,
            repair_passes=12,
        )
    else:
        raise ValueError(f"Unknown planner: {planner_name}")
    runtime_ms = (perf_counter() - start) * 1000.0
    return route, runtime_ms


def _protocol_counts(scenario) -> dict[str, int]:
    counts = {name: 0 for name in scenario.protocols}
    for node in scenario.nodes.values():
        counts[node.protocol] = counts.get(node.protocol, 0) + 1
    return counts


def _run_raw() -> list[dict[str, object]]:
    planners = (
        "distance_only",
        "ordinary_collection",
        "protocol_aware",
        "bounded_blackout",
        "genetic_algorithm",
        "particle_swarm",
        "ga_blackout",
        "pso_blackout",
        "q_learning_blackout",
        "neural_q_blackout",
        "am_ppo",
        "am_ppo_plus_ls",
    )
    rows: list[dict[str, object]] = []

    for scenario_seed in SCENARIO_SEEDS:
        scenario = build_random_scenario(seed=scenario_seed, node_count=14)
        counts = _protocol_counts(scenario)
        for planner in planners:
            route, runtime_ms = _route_with_runtime(planner, scenario_seed, scenario)
            result = simulate_route(scenario, route)
            rows.append(
                {
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
                    "wait_time_s": round(result.wait_time_s, 3),
                    "service_time_s": round(result.service_time_s, 3),
                    "protocol_switches": result.protocol_switches,
                    "radio_obstacle_hits": result.radio_obstacle_hits,
                    "mission_feasible": result.mission_feasible,
                    "runtime_ms": round(runtime_ms, 3),
                    "route": " -> ".join(route),
                }
            )

    return rows


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _summarize(raw_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    def _as_bool(value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes"}

    planners = sorted({str(row["planner"]) for row in raw_rows})
    scenario_groups: dict[str, list[dict[str, object]]] = {}
    for row in raw_rows:
        scenario_groups.setdefault(str(row["scenario"]), []).append(row)
    summary = []
    for planner in planners:
        group = [row for row in raw_rows if row["planner"] == planner]
        blackout_wins = 0
        for rows in scenario_groups.values():
            best = min(float(row["max_blackout_s"]) for row in rows)
            value = float(next(row["max_blackout_s"] for row in rows if row["planner"] == planner))
            if abs(value - best) <= 1e-9:
                blackout_wins += 1
        item: dict[str, object] = {
            "planner": planner,
            "scenarios": len(group),
            "blackout_wins": blackout_wins,
            "violations_90s": sum(float(row["max_blackout_s"]) > 90.0 + 1e-9 for row in group),
            "endurance_violations": sum(not _as_bool(row["mission_feasible"]) for row in group),
            "joint_violations": sum(
                float(row["max_blackout_s"]) > 90.0 + 1e-9
                or not _as_bool(row["mission_feasible"])
                for row in group
            ),
        }
        for key in (
            "total_time_s",
            "flight_distance_m",
            "max_blackout_s",
            "wait_time_s",
            "service_time_s",
            "protocol_switches",
            "radio_obstacle_hits",
            "runtime_ms",
        ):
            values = [float(row[key]) for row in group]
            item[f"{key}_mean"] = round(_mean(values), 3)
            item[f"{key}_std"] = round(_std(values), 3)
            item[f"{key}_ci95"] = round(1.96 * item[f"{key}_std"] / math.sqrt(len(values)), 3)
        summary.append(item)
    return summary


def _write_markdown(summary: list[dict[str, object]], path: Path) -> None:
    lines = [
        f"# Ad Hoc Networks Multi-Scenario Simulation Suite - {REPORT_DATE}",
        "",
        f"This suite averages results over {len(SCENARIO_SEEDS)} randomly generated heterogeneous IoT sensor-network scenarios with 14 nodes per scenario.",
        "",
        *markdown_table(
            summary,
            [
                ("Planner", "planner"),
                ("Scenarios", "scenarios"),
                ("Time mean", "total_time_s_mean"),
                ("Time std", "total_time_s_std"),
                ("Max blackout mean", "max_blackout_s_mean"),
                ("Max blackout std", "max_blackout_s_std"),
                ("Max blackout 95% CI", "max_blackout_s_ci95"),
                ("90s viol.", "violations_90s"),
                ("Endurance viol.", "endurance_violations"),
                ("Joint viol.", "joint_violations"),
                ("Blackout wins", "blackout_wins"),
                ("Switches mean", "protocol_switches_mean"),
                ("Runtime mean ms", "runtime_ms_mean"),
            ],
        ),
        "",
        "## Reading Notes",
        "",
        "- `ordinary_collection` models a conventional mobile-collector route that accounts for payload size but ignores protocol-specific sleep, switching, reconnection, and radio-obstacle effects.",
        "- `protocol_aware` minimizes mission time. `bounded_blackout` returns the fastest evaluated candidate satisfying both the 90 s blackout budget and mission endurance; when none is jointly feasible, it returns a flagged diagnostic candidate using the deterministic violation/blackout/time fallback.",
        "- `genetic_algorithm` and `particle_swarm` are time-oriented population baselines using the protocol-aware objective.",
        "- `ga_blackout` and `pso_blackout` are objective-matched population baselines that directly minimize maximum blackout, breaking ties by mission time.",
        "- `q_learning_blackout` and `neural_q_blackout` report the learning policy followed by an explicitly configured blackout-first local-search repair.",
        "- `am_ppo` is the raw adapted action-masked PPO policy; `am_ppo_plus_ls` applies the same 12-pass repair used by the neural-Q hybrid. The pair separates learned-policy quality from post-processing.",
        "- Runtime is measured on the local machine and should be reported as implementation-level evidence, not hardware-independent complexity.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    raw_path = ROOT / "results" / f"adhoc_multiscenario_raw_{REPORT_DATE}.csv"
    if "--summarize-only" in sys.argv:
        with raw_path.open(newline="", encoding="utf-8") as handle:
            raw_rows = list(csv.DictReader(handle))
    else:
        raw_rows = _run_raw()
    summary = _summarize(raw_rows)

    summary_path = ROOT / "results" / f"adhoc_multiscenario_summary_{REPORT_DATE}.csv"
    md_path = ROOT / "results" / f"adhoc_multiscenario_summary_{REPORT_DATE}.md"
    if "--summarize-only" not in sys.argv:
        write_csv(raw_rows, raw_path)
    write_csv(summary, summary_path)
    _write_markdown(summary, md_path)

    print(f"Wrote {raw_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
