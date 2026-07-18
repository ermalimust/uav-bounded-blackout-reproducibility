# Small Exact Benchmark - 2026-07-18

Exhaustive enumeration over 12 random 8-node scenarios with blackout budget beta = 90 s.

| Planner | Time (s) | Max blackout (s) | Viol. | Exact matches | Feasible time gap (%) | Mean B gap (s) | Max B gap (s) | Max viol. (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| exact_bounded | 592.841 | 65.574 | 0 | 12 | 0.0 | 0.0 | 0.0 | 0.0 |
| bounded_blackout | 629.555 | 65.074 | 0 | 3 | 5.867 | -0.5 | 20.839 | 0.0 |
| protocol_aware | 628.237 | 76.269 | 3 | 2 | 4.814 | 10.694 | 44.755 | 21.902 |
| genetic_algorithm | 630.896 | 75.218 | 3 | 2 | 5.478 | 9.644 | 42.755 | 21.902 |
| particle_swarm | 627.979 | 74.744 | 3 | 1 | 5.095 | 9.17 | 44.755 | 21.902 |
| ga_blackout | 671.168 | 66.135 | 0 | 1 | 13.349 | 0.561 | 32.29 | 0.0 |
| pso_blackout | 645.779 | 63.507 | 1 | 2 | 8.689 | -2.068 | 22.218 | 13.041 |
| distance_only | 921.065 | 154.028 | 10 | 0 | 24.024 | 88.453 | 169.885 | 139.334 |
| ordinary_collection | 951.462 | 159.179 | 11 | 0 | 39.489 | 93.604 | 174.342 | 141.607 |

Notes:
- `exact_bounded` is the fastest enumerated route satisfying both the 90 s blackout budget and mission endurance, or the minimum-blackout route if the joint constraints are infeasible.
- `mean_feasible_time_gap_pct` is computed only on scenarios where both the planner and the exact route satisfy both constraints.
- `mean_blackout_gap_s` is relative to the exact bounded solution in the same scenario.
