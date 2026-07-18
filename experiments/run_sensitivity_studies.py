from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.experiment_utils import markdown_table, planner_rows, write_csv
from experiments.scenario_variants import blackout_variant, protocol_ratio_variant
from uav_protocol_planning.scenarios import build_reference_scenario


REPORT_DATE = "2026-07-18"


def _summarize_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    numeric_keys = [
        "total_time_s",
        "flight_distance_m",
        "success_rate",
        "max_blackout_s",
        "reconnect_count",
        "protocol_switches",
        "radio_obstacle_hits",
    ]
    groups: dict[tuple[str, float, str], list[dict[str, object]]] = {}
    for row in rows:
        key = (str(row["study"]), float(row["value"]), str(row["planner"]))
        groups.setdefault(key, []).append(row)

    summary = []
    for (study, value, planner), group_rows in sorted(groups.items()):
        item: dict[str, object] = {
            "scenario": f"{study}_{value:g}",
            "planner": planner,
            "study": study,
            "parameter": group_rows[0]["parameter"],
            "value": value,
            "replicates": len(group_rows),
            "route": "",
        }
        for key in numeric_keys:
            item[key] = round(
                sum(float(row[key]) for row in group_rows) / len(group_rows),
                3,
            )
        summary.append(item)
    return summary


def _write_markdown(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ratio_rows = [row for row in rows if row["study"] == "protocol_ratio"]
    blackout_rows = [row for row in rows if row["study"] == "blackout_threshold"]

    columns = [
        ("Value", "value"),
        ("Planner", "planner"),
        ("Time (s)", "total_time_s"),
        ("Distance (m)", "flight_distance_m"),
        ("Max blackout (s)", "max_blackout_s"),
        ("Switches", "protocol_switches"),
        ("Radio hits", "radio_obstacle_hits"),
    ]

    lines = [
        f"# Sensitivity Study Result - {REPORT_DATE}",
        "",
        "## Protocol Heterogeneity Ratio",
        "",
        *markdown_table(ratio_rows, columns),
        "",
        "## Maximum Blackout Threshold",
        "",
        *markdown_table(blackout_rows, columns),
        "",
        "## Reading Notes",
        "",
        "- `protocol_ratio` changes the fraction of nodes that keep their original LoRa/ZigBee/BLE/WiFi profiles; the rest use one generic protocol.",
        "- `blackout_threshold` changes the maximum blackout target used by the planner objective.",
        "- These fixed-layout sweeps are trend diagnostics rather than population-level statistical claims; the separate random-scenario analyses provide the inferential evidence.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    base = build_reference_scenario()
    raw_rows: list[dict[str, object]] = []

    for ratio in (0.0, 0.25, 0.5, 0.75, 1.0):
        for replicate, seed in enumerate((11,)):
            scenario = protocol_ratio_variant(base, ratio, seed=seed)
            raw_rows.extend(
                planner_rows(
                    f"protocol_ratio_{ratio:.2f}_rep{replicate}",
                    scenario,
                    extra={
                        "study": "protocol_ratio",
                        "parameter": "heterogeneity_ratio",
                        "value": ratio,
                        "replicate": replicate,
                    },
                    ga_population_size=20,
                    ga_generations=40,
                )
            )

    for target_s in (45.0, 60.0, 75.0, 90.0, 120.0, 150.0):
        scenario = blackout_variant(base, target_s)
        raw_rows.extend(
            planner_rows(
                f"blackout_threshold_{int(target_s)}s",
                scenario,
                extra={
                    "study": "blackout_threshold",
                    "parameter": "max_blackout_s",
                    "value": target_s,
                    "replicate": 0,
                },
                blackout_budget_s=target_s,
            )
        )

    rows = _summarize_rows(raw_rows)
    raw_path = ROOT / "results" / f"sensitivity_experiment_raw_{REPORT_DATE}.csv"
    csv_path = ROOT / "results" / f"sensitivity_experiment_{REPORT_DATE}.csv"
    md_path = ROOT / "results" / f"sensitivity_experiment_{REPORT_DATE}.md"
    write_csv(raw_rows, raw_path)
    write_csv(rows, csv_path)
    _write_markdown(rows, md_path)

    print(f"Wrote {raw_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
