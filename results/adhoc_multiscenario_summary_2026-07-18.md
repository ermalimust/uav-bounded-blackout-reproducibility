# Ad Hoc Networks Multi-Scenario Simulation Suite - 2026-07-18

This suite averages results over 50 randomly generated heterogeneous IoT sensor-network scenarios with 14 nodes per scenario.

| Planner | Scenarios | Time mean | Time std | Max blackout mean | Max blackout std | Max blackout 95% CI | 90s viol. | Endurance viol. | Joint viol. | Blackout wins | Switches mean | Runtime mean ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| am_ppo | 50 | 1245.353 | 290.011 | 136.371 | 51.178 | 14.186 | 40 | 9 | 40 | 0 | 7.5 | 1375.529 |
| am_ppo_plus_ls | 50 | 1260.957 | 256.439 | 83.384 | 23.945 | 6.637 | 19 | 6 | 19 | 6 | 9.16 | 1383.648 |
| bounded_blackout | 50 | 1084.915 | 216.487 | 63.808 | 13.434 | 3.724 | 1 | 2 | 2 | 23 | 9.6 | 1836.873 |
| distance_only | 50 | 1563.68 | 379.819 | 162.352 | 48.743 | 13.511 | 47 | 26 | 47 | 0 | 9.82 | 0.024 |
| ga_blackout | 50 | 1169.402 | 219.305 | 65.712 | 9.735 | 2.698 | 0 | 2 | 2 | 17 | 9.22 | 1204.039 |
| genetic_algorithm | 50 | 1150.509 | 220.96 | 86.257 | 17.796 | 4.933 | 21 | 3 | 22 | 2 | 9.42 | 687.514 |
| neural_q_blackout | 50 | 1294.08 | 248.503 | 85.616 | 22.968 | 6.366 | 15 | 7 | 16 | 2 | 9.24 | 2176.358 |
| ordinary_collection | 50 | 1544.249 | 332.783 | 169.963 | 41.979 | 11.636 | 48 | 27 | 48 | 0 | 9.74 | 14.364 |
| particle_swarm | 50 | 1142.694 | 226.11 | 88.548 | 16.006 | 4.437 | 21 | 3 | 23 | 1 | 9.02 | 236.445 |
| protocol_aware | 50 | 1133.389 | 215.226 | 89.236 | 22.985 | 6.371 | 22 | 2 | 23 | 2 | 9.1 | 301.231 |
| pso_blackout | 50 | 1165.364 | 211.3 | 64.526 | 9.725 | 2.696 | 0 | 2 | 2 | 21 | 9.36 | 737.227 |
| q_learning_blackout | 50 | 1382.194 | 235.184 | 111.82 | 34.063 | 9.442 | 33 | 13 | 34 | 1 | 8.82 | 43.228 |

## Reading Notes

- `ordinary_collection` models a conventional mobile-collector route that accounts for payload size but ignores protocol-specific sleep, switching, reconnection, and radio-obstacle effects.
- `protocol_aware` minimizes mission time and `bounded_blackout` returns the fastest evaluated candidate satisfying a 90 s blackout budget, or the minimum-blackout candidate when no evaluated route satisfies the budget.
- `genetic_algorithm` and `particle_swarm` are time-oriented population baselines using the protocol-aware objective.
- `ga_blackout` and `pso_blackout` are objective-matched population baselines that directly minimize maximum blackout, breaking ties by mission time.
- `q_learning_blackout` and `neural_q_blackout` report the learning policy followed by an explicitly configured blackout-first local-search repair.
- `am_ppo` is the raw adapted action-masked PPO policy; `am_ppo_plus_ls` applies the same 12-pass repair used by the neural-Q hybrid. The pair separates learned-policy quality from post-processing.
- Runtime is measured on the local machine and should be reported as implementation-level evidence, not hardware-independent complexity.
