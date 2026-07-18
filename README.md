# Protocol-Aware Bounded-Blackout Routing

This repository is the reproducibility package for the study:

**Protocol-Aware Bounded-Blackout Routing for UAV-Assisted Heterogeneous IoT Sensor Networks**

It contains the event-driven route evaluator, all compared planners, deterministic experiment drivers, unit tests, and the dated result tables used in the revised manuscript. The package covers the 50-scenario comparison, paired statistical checks, a small exact benchmark, parameter sensitivity, phase perturbation, uncertainty, scalability, and two measurement-informed protocol-profile diagnostics.

## Scope and Claim Boundary

The core experiments evaluate a reference heterogeneous IoT mission in simulation. Public and literature measurement sources define additional evidence-informed planning envelopes rather than fitted target-system models.

This package does **not** claim closed-loop UAV flight validation, field-proven timing guarantees, or universal dominance. The public and literature profiles are robustness diagnostics for the route scheduler, not substitutes for onboard execution and live aerial packet-delivery experiments.

## Repository Layout

```text
experiments/
  run_q1_simulation_suite.py              50-scenario main comparison
  run_statistical_checks.py               paired bootstrap/sign tests
  run_small_exact_benchmark.py            exact 8-node benchmark
  run_protocol_parameter_sensitivity.py   range/recovery sensitivity
  run_phase_perturbation_study.py          protocol-clock phase offsets
  run_uncertainty_robustness.py            parameter perturbations
  run_scalability_study.py                 node-count/runtime study
  run_public_measurement_profile.py        public-measurement profile check
  run_literature_profile_robustness.py     literature-profile check
  run_task_driven_gap_checks.py            objective-substitution checks
  run_reference_comparison.py              reference-case route table
  run_ablation_study.py                    component ablations
src/uav_protocol_planning/
  models.py                                scenario and state structures
  scenarios.py                             reference and diagnostic profiles
  simulation.py                            event-driven route evaluator
  planners.py                              all compared route planners
  metrics.py                               temporal route metrics
results/                                   dated raw and summary outputs
tests/test_simulation.py                   evaluator/planner unit tests
DATA_SOURCES.md                            external-source claim boundary
CITATION.cff
LICENSE
```

## Requirements

The experiment drivers use only the Python standard library.

- Python 3.10 or newer
- Windows PowerShell, macOS Terminal, or Linux shell

## Quick Start

From the repository root, expose the source package and run the unit tests:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

Run the principal simulation and statistical checks:

```powershell
python experiments/run_q1_simulation_suite.py
python experiments/run_statistical_checks.py
python experiments/run_small_exact_benchmark.py
python experiments/run_public_measurement_profile.py
```

The scripts write regenerated CSV and Markdown outputs to `results/`. Population-based searches are deterministic for the checked-in seeds but can take minutes; the larger scalability settings can take substantially longer.

## Expected Headline Outputs

The checked-in main outputs were generated on 2026-07-18 for 50 random 14-node scenarios with seeds 101--150.

| Planner | Mean mission time (s) | Mean maximum blackout (s) | Joint violations | Blackout wins |
| --- | ---: | ---: | ---: | ---: |
| bounded-blackout | 1084.915 | 63.808 | 2 | 23 |
| protocol-aware time minimization | 1133.389 | 89.236 | 23 | 10 |
| GA, bounded selection | 1169.402 | 65.712 | 2 | 17 |
| PSO, bounded selection | 1165.364 | 64.526 | 2 | 21 |
| Q-learning + local search | 1382.194 | 111.820 | 34 | 4 |
| neural Q-learning + local search | 1294.080 | 85.616 | 16 | 9 |
| action-masked PPO, raw | 1245.353 | 136.371 | 40 | 3 |
| action-masked PPO + local search | 1260.957 | 83.384 | 19 | 7 |

The bounded-blackout planner reduces mean maximum blackout by 25.428 s relative to protocol-aware time minimization in the paired study (34 wins, 0 ties, 16 losses; two-sided sign-test p = 1.16e-10). Relative to the bounded GA and PSO variants, the mean differences are small and not statistically significant in this sample.

In the 12-scenario exact 8-node benchmark, the bounded heuristic has zero joint violations, matches the exact route three times, and has a mean feasible mission-time gap of 5.867%.

The public-measurement-informed profile rerun uses the same 50 seeds and the same joint blackout/endurance filter as the manuscript. Its checked-in 2026-07-18 summary is:

| Planner | Mean mission time (s) | Mean maximum blackout (s) | Blackout violations | Endurance violations | Joint violations |
| --- | ---: | ---: | ---: | ---: | ---: |
| bounded-blackout | 2105.355 | 76.160 | 10 | 38 | 38 |
| protocol-aware time minimization | 2156.889 | 97.159 | 26 | 40 | 43 |
| genetic algorithm | 2181.895 | 96.465 | 32 | 42 | 46 |
| particle swarm | 2175.532 | 93.969 | 30 | 41 | 44 |

These rows are a profile-robustness and mission-partition diagnostic, not a field-validation or single-sortie-feasibility claim. The complete raw and summary tables are stored under `results/public_measurement_*_2026-07-18.*`.

## External Measurement Sources

Raw third-party datasets are not redistributed. See `DATA_SOURCES.md` for the cited sources and the limited role they play in defining measurement-informed profile envelopes.

## License

The source code in this repository is released under the MIT License. The result tables and documentation are additionally available under CC BY 4.0. See `LICENSE` for details. External measurement datasets referenced in `DATA_SOURCES.md` remain under their own licenses at their original sources.

## Citation

See `CITATION.cff`.
