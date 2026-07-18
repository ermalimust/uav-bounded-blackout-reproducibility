from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.experiment_utils import markdown_table, planner_rows, write_csv
from uav_protocol_planning.models import ProtocolProfile, Scenario
from uav_protocol_planning.scenarios import build_reference_scenario


REPORT_DATE = "2026-07-18"


def _scale_protocols(
    scenario: Scenario,
    parameter: str,
    factor: float,
) -> Scenario:
    protocols: dict[str, ProtocolProfile] = {}
    for name, profile in scenario.protocols.items():
        if parameter == "data_rate_factor":
            protocols[name] = replace(profile, data_rate_kbps=profile.data_rate_kbps * factor)
        elif parameter == "range_factor":
            protocols[name] = replace(profile, nominal_range_m=profile.nominal_range_m * factor)
        elif parameter == "setup_cost_factor":
            protocols[name] = replace(
                profile,
                connection_setup_s=profile.connection_setup_s * factor,
                reconnect_penalty_s=profile.reconnect_penalty_s * factor,
                switch_penalty_s=profile.switch_penalty_s * factor,
            )
        elif parameter == "sleep_cycle_factor":
            protocols[name] = replace(profile, sleep_cycle_s=profile.sleep_cycle_s * factor)
        elif parameter == "loss_factor":
            protocols[name] = replace(
                profile,
                packet_loss_at_edge=min(0.9, profile.packet_loss_at_edge * factor),
            )
        elif parameter == "recovery_threshold_factor":
            protocols[name] = replace(
                profile,
                recovery_threshold_s=max(0.1, profile.recovery_threshold_s * factor),
            )
        else:
            raise ValueError(f"Unknown sensitivity parameter: {parameter}")

    return replace(
        scenario,
        name=f"{scenario.name}_{parameter}_{factor:.2f}",
        protocols=protocols,
    )


def _write_markdown(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        ("Parameter", "parameter"),
        ("Factor", "value"),
        ("Planner", "planner"),
        ("Time (s)", "total_time_s"),
        ("Max blackout (s)", "max_blackout_s"),
        ("Wait (s)", "wait_time_s"),
        ("Service (s)", "service_time_s"),
        ("Switches", "protocol_switches"),
    ]
    lines = [
        f"# Protocol Parameter Sensitivity - {REPORT_DATE}",
        "",
        "Reference scenario sensitivity over communication-layer parameters.",
        "",
        *markdown_table(rows, columns),
        "",
        "## Reading Notes",
        "",
        "- `data_rate_factor` scales every protocol data rate.",
        "- `range_factor` scales every nominal contact radius; route travel changes because service begins at the first feasible contact point.",
        "- `setup_cost_factor` scales connection setup, reconnection, and protocol-switch cost.",
        "- `sleep_cycle_factor` lengthens or shortens sleep cycles while keeping awake windows fixed.",
        "- `loss_factor` scales packet loss at the communication edge.",
        "- `recovery_threshold_factor` scales the protocol-interface inactivity thresholds `gamma_a`.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    base = build_reference_scenario()
    parameters = (
        "data_rate_factor",
        "range_factor",
        "setup_cost_factor",
        "sleep_cycle_factor",
        "loss_factor",
        "recovery_threshold_factor",
    )
    factors = (0.5, 1.0, 1.5, 2.0)
    rows: list[dict[str, object]] = []

    for parameter in parameters:
        for factor in factors:
            scenario = _scale_protocols(base, parameter, factor)
            rows.extend(
                planner_rows(
                    f"{parameter}_{factor:.2f}",
                    scenario,
                    extra={
                        "study": "protocol_parameter",
                        "parameter": parameter,
                        "value": factor,
                    },
                    ga_population_size=20,
                    ga_generations=40,
                    pso_swarm_size=20,
                    pso_iterations=45,
                )
            )

    csv_path = ROOT / "results" / f"protocol_parameter_sensitivity_{REPORT_DATE}.csv"
    md_path = ROOT / "results" / f"protocol_parameter_sensitivity_{REPORT_DATE}.md"
    write_csv(rows, csv_path)
    _write_markdown(rows, md_path)
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
