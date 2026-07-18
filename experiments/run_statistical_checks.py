from __future__ import annotations

import csv
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.experiment_utils import markdown_table, write_csv


REPORT_DATE = "2026-07-18"
RAW_RANDOM_SUITE = ROOT / "results" / "adhoc_multiscenario_raw_2026-07-18.csv"
TARGET = "bounded_blackout"
COMPARATORS = (
    "distance_only",
    "ordinary_collection",
    "protocol_aware",
    "genetic_algorithm",
    "particle_swarm",
    "ga_blackout",
    "pso_blackout",
    "q_learning_blackout",
    "neural_q_blackout",
    "am_ppo",
    "am_ppo_plus_ls",
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _normal_ci(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    mean = sum(values) / len(values)
    if len(values) == 1:
        return mean, 0.0
    std = math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))
    return mean, 1.96 * std / math.sqrt(len(values))


def _two_sided_sign_p_value(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def summarize(raw_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_scenario: dict[str, dict[str, dict[str, str]]] = {}
    for row in raw_rows:
        by_scenario.setdefault(row["scenario"], {})[row["planner"]] = row

    summary: list[dict[str, object]] = []
    for comparator in COMPARATORS:
        diffs: list[float] = []
        wins = losses = ties = 0
        for planners in by_scenario.values():
            if TARGET not in planners or comparator not in planners:
                continue
            target_b = float(planners[TARGET]["max_blackout_s"])
            comp_b = float(planners[comparator]["max_blackout_s"])
            diff = comp_b - target_b
            diffs.append(diff)
            if diff > 1e-9:
                wins += 1
            elif diff < -1e-9:
                losses += 1
            else:
                ties += 1

        mean_diff, ci95 = _normal_ci(diffs)
        summary.append(
            {
                "target": TARGET,
                "comparator": comparator,
                "scenarios": len(diffs),
                "mean_blackout_reduction_s": round(mean_diff, 3),
                "ci95_s": round(ci95, 3),
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "sign_test_p": f"{_two_sided_sign_p_value(wins, losses):.3g}",
            }
        )
    return summary


def write_markdown(summary: list[dict[str, object]], path: Path) -> None:
    lines = [
        f"# Paired Statistical Checks - {REPORT_DATE}",
        "",
        "Paired comparisons use the 50-scenario Ad Hoc Networks random suite. Positive mean reduction means the comparator's maximum blackout is higher than bounded-blackout on the same scenario. The sign test is two-sided and ignores exact ties.",
        "",
        *markdown_table(
            summary,
            [
                ("Target", "target"),
                ("Comparator", "comparator"),
                ("Scenarios", "scenarios"),
                ("Mean B reduction (s)", "mean_blackout_reduction_s"),
                ("95% CI (s)", "ci95_s"),
                ("Wins", "wins"),
                ("Losses", "losses"),
                ("Ties", "ties"),
                ("Sign-test p", "sign_test_p"),
            ],
        ),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    raw_rows = _read_rows(RAW_RANDOM_SUITE)
    summary = summarize(raw_rows)
    results_dir = ROOT / "results"
    write_csv(summary, results_dir / f"statistical_checks_{REPORT_DATE}.csv")
    write_markdown(summary, results_dir / f"statistical_checks_{REPORT_DATE}.md")
    print("Wrote paired statistical checks.")


if __name__ == "__main__":
    main()
