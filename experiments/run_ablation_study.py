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
from experiments.scenario_variants import (
    always_awake,
    blackout_variant,
    homogeneous_protocols,
    without_radio_obstacles,
)
from uav_protocol_planning.scenarios import build_reference_scenario


REPORT_DATE = "2026-07-18"


def _write_markdown(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Ablation Study Result - {REPORT_DATE}",
        "",
        *markdown_table(
            rows,
            [
                ("Scenario", "scenario"),
                ("Planner", "planner"),
                ("Time (s)", "total_time_s"),
                ("Distance (m)", "flight_distance_m"),
                ("Success", "success_rate"),
                ("Max blackout (s)", "max_blackout_s"),
                ("Reconnects", "reconnect_count"),
                ("Switches", "protocol_switches"),
                ("Radio hits", "radio_obstacle_hits"),
            ],
        ),
    ]
    lines.extend(
        [
            "",
            "## Reading Notes",
            "",
            "- `homogeneous_protocols` removes protocol differences to test whether the claimed benefit depends on heterogeneity.",
            "- `no_sleep` isolates intermittent connectivity.",
            "- `no_radio_obstacles` isolates protocol-specific invisible obstacles.",
            "- `blackout_*s` variants test whether a stricter maximum blackout target changes route selection.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    base = build_reference_scenario()
    scenarios = [
        ("reference", base, 90.0),
        ("homogeneous_protocols", homogeneous_protocols(base), 90.0),
        ("no_sleep", always_awake(base), 90.0),
        ("no_radio_obstacles", without_radio_obstacles(base), 90.0),
        ("blackout_45s", blackout_variant(base, 45.0), 45.0),
        ("blackout_60s", blackout_variant(base, 60.0), 60.0),
        ("blackout_75s", blackout_variant(base, 75.0), 75.0),
        ("blackout_120s", blackout_variant(base, 120.0), 120.0),
    ]

    rows: list[dict[str, object]] = []
    for label, scenario, budget_s in scenarios:
        rows.extend(
            planner_rows(label, scenario, blackout_budget_s=budget_s)
        )

    csv_path = ROOT / "results" / f"ablation_experiment_{REPORT_DATE}.csv"
    md_path = ROOT / "results" / f"ablation_experiment_{REPORT_DATE}.md"
    write_csv(rows, csv_path)
    _write_markdown(rows, md_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
