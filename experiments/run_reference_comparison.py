from __future__ import annotations

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
from uav_protocol_planning.scenarios import build_reference_scenario
from uav_protocol_planning.simulation import simulate_route

REPORT_DATE = "2026-07-18"
BUDGET_S = 90.0


def main() -> None:
    scenario = build_reference_scenario()
    constructors = {
        "distance_only": lambda: distance_only_route(scenario),
        "ordinary_collection": lambda: ordinary_data_collection_route(scenario),
        "protocol_aware": lambda: protocol_aware_route(scenario, blackout_weight=0.0),
        "bounded_blackout": lambda: bounded_blackout_route(scenario, budget=BUDGET_S),
        "genetic_algorithm": lambda: genetic_algorithm_route(
            scenario, blackout_weight=3.0, population_size=20, generations=40, seed=1101
        ),
        "particle_swarm": lambda: particle_swarm_route(
            scenario, blackout_weight=3.0, swarm_size=20, iterations=45, seed=2101
        ),
        "ga_blackout": lambda: genetic_algorithm_blackout_route(
            scenario, population_size=20, generations=40, seed=3101
        ),
        "pso_blackout": lambda: particle_swarm_blackout_route(
            scenario, swarm_size=20, iterations=45, seed=4101
        ),
        "q_learning_plus_ls": lambda: q_learning_blackout_route(
            scenario, budget=BUDGET_S, episodes=320, seed=5101, repair_passes=8
        ),
        "neural_q_plus_ls": lambda: neural_q_blackout_route(
            scenario, budget=BUDGET_S, episodes=220, hidden_size=24,
            batch_size=16, seed=6101, repair_passes=12
        ),
        "am_ppo": lambda: action_masked_ppo_route(
            scenario, budget=BUDGET_S, episodes=360, hidden_size=24,
            update_epochs=3, seed=7101, repair_passes=0
        ),
        "am_ppo_plus_ls": lambda: action_masked_ppo_route(
            scenario, budget=BUDGET_S, episodes=360, hidden_size=24,
            update_epochs=3, seed=7101, repair_passes=12
        ),
    }
    rows: list[dict[str, object]] = []
    for planner, constructor in constructors.items():
        started = perf_counter()
        route = constructor()
        runtime_ms = (perf_counter() - started) * 1000.0
        result = simulate_route(scenario, route)
        rows.append(
            {
                "planner": planner,
                "total_time_s": round(result.total_time_s, 3),
                "flight_distance_m": round(result.flight_distance_m, 3),
                "max_blackout_s": round(result.max_blackout_s, 3),
                "meets_90s_budget": int(result.max_blackout_s <= BUDGET_S + 1e-9),
                "mission_feasible": int(result.mission_feasible),
                "protocol_switches": result.protocol_switches,
                "runtime_ms": round(runtime_ms, 3),
                "route": " -> ".join(route),
            }
        )

    sweep = []
    for budget in (120.0, 110.0, 90.0, 70.0, 50.0):
        route = bounded_blackout_route(scenario, budget=budget)
        result = simulate_route(scenario, route)
        sweep.append(
            {
                "budget_s": budget,
                "total_time_s": round(result.total_time_s, 3),
                "max_blackout_s": round(result.max_blackout_s, 3),
                "meets_budget": int(result.max_blackout_s <= budget + 1e-9),
                "mission_feasible": int(result.mission_feasible),
                "route": " -> ".join(route),
            }
        )

    write_csv(rows, ROOT / "results" / f"reference_comparison_{REPORT_DATE}.csv")
    write_csv(sweep, ROOT / "results" / f"reference_budget_sweep_{REPORT_DATE}.csv")
    lines = [
        f"# Reference Comparison - {REPORT_DATE}",
        "",
        *markdown_table(rows, [
            ("Planner", "planner"), ("Time", "total_time_s"),
            ("Distance", "flight_distance_m"), ("Max blackout", "max_blackout_s"),
            ("B<=90", "meets_90s_budget"), ("T<=1500", "mission_feasible"),
            ("Switches", "protocol_switches"), ("Runtime ms", "runtime_ms"),
        ]),
        "", "## Budget sweep", "",
        *markdown_table(sweep, [
            ("Budget", "budget_s"), ("Time", "total_time_s"),
            ("Max blackout", "max_blackout_s"), ("Meets budget", "meets_budget"),
            ("T<=1500", "mission_feasible"),
        ]),
    ]
    (ROOT / "results" / f"reference_comparison_{REPORT_DATE}.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
