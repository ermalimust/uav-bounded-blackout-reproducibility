# Protocol-Aware Bounded-Blackout Routing

This repository contains the reproducibility package for the public measurement-trace calibrated profile experiments associated with the study:

**Protocol-Aware Bounded-Blackout Routing for UAV-Assisted Heterogeneous IoT Sensor Networks**

The package focuses on the routing simulator, the calibrated protocol profile, the public-trace rerun script, and the result tables used to check whether the maximum-blackout conclusion is robust to externally grounded LoRa and ZigBee-class radio inputs.

## Scope

This package reproduces the public measurement-trace calibrated profile check. It uses public measurement evidence to calibrate scheduler-visible protocol fields such as nominal range and near-edge packet loss, then reruns the routing comparison under that profile.

This package does **not** claim to be a closed-loop UAV flight experiment. The public measurement traces calibrate the simulator inputs; they do not validate onboard route execution, controller timing, or live packet delivery on an aerial platform.

## Repository Layout

```text
experiments/
  run_public_trace_calibration.py   Main rerun script
  experiment_utils.py               CSV and table helpers
src/uav_protocol_planning/
  models.py                         Scenario and protocol data structures
  scenarios.py                      Reference and public-trace profile builders
  simulation.py                     Route evaluator
  planners.py                       Compared route planners
  metrics.py                        Temporal route metrics
results/
  public_trace_profile_table_2026-07-04.csv
  public_trace_multiscenario_summary_2026-07-04.csv
  public_trace_multiscenario_raw_2026-07-04.csv
  public_trace_metric_checks_summary_2026-07-04.csv
  public_trace_metric_checks_raw_2026-07-04.csv
  public_trace_calibration_2026-07-04.md
tests/
  test_public_trace_smoke.py
DATA_SOURCES.md
CITATION.cff
LICENSE_PENDING.md
```

## Requirements

The public-trace rerun uses only the Python standard library.

Recommended environment:

- Python 3.10 or newer
- Windows PowerShell, macOS Terminal, or Linux shell

## Quick Start

From the repository root:

```powershell
python experiments/run_public_trace_calibration.py
```

The script writes the regenerated CSV and Markdown outputs to `results/`.
The full 50-scenario rerun can take several minutes because it includes population-based and bounded-blackout route searches.

Run the smoke test:

```powershell
python -m unittest tests/test_public_trace_smoke.py
```

## Expected Headline Outputs

The checked-in outputs were produced on 2026-07-04 using 50 random 14-node scenarios with seeds 101--150.

Main public-trace rerun:

| Planner | Mean maximum blackout (s) | 90 s violations |
| --- | ---: | ---: |
| bounded-blackout | 78.0 | 8 |
| protocol-aware time minimization | 111.2 | 37 |
| genetic algorithm | 103.7 | 41 |
| particle swarm | 101.0 | 38 |

Average/penalty/freshness checks under the same calibrated profile:

| Planner | Mean maximum blackout (s) | 90 s violations |
| --- | ---: | ---: |
| bounded-blackout, beta = 90 s | 78.6 | 8 |
| soft penalty, w = 12 | 89.3 | 21 |
| average-gap | 101.7 | 34 |
| freshness-focused | 200.5 | 48 |

The 78.0 s and 78.6 s bounded-blackout rows come from different route-construction checks under the same calibrated profile: the main router-family rerun and the objective-substitution check.

## External Measurement Sources

The raw external measurement datasets are not redistributed here. See `DATA_SOURCES.md` for the cited public sources and how they are used. The repository stores the calibrated profile values and rerun outputs, not a mirrored copy of third-party datasets.

## License

No public reuse license has been selected for this package yet. See `LICENSE_PENDING.md`.

## Citation

See `CITATION.cff`.
