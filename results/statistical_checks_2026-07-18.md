# Paired Statistical Checks - 2026-07-18

Paired comparisons use the 50-scenario Ad Hoc Networks random suite. Positive mean reduction means the comparator's maximum blackout is higher than bounded-blackout on the same scenario. The sign test is two-sided and ignores exact ties.

| Target | Comparator | Scenarios | Mean B reduction (s) | 95% CI (s) | Wins | Losses | Ties | Sign-test p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bounded_blackout | distance_only | 50 | 98.544 | 12.775 | 50 | 0 | 0 | 1.78e-15 |
| bounded_blackout | ordinary_collection | 50 | 106.155 | 12.059 | 49 | 0 | 1 | 3.55e-15 |
| bounded_blackout | protocol_aware | 50 | 25.428 | 7.27 | 34 | 0 | 16 | 1.16e-10 |
| bounded_blackout | genetic_algorithm | 50 | 22.449 | 6.52 | 36 | 7 | 7 | 8.96e-06 |
| bounded_blackout | particle_swarm | 50 | 24.741 | 5.446 | 42 | 3 | 5 | 8.65e-10 |
| bounded_blackout | ga_blackout | 50 | 1.905 | 4.516 | 24 | 17 | 9 | 0.349 |
| bounded_blackout | pso_blackout | 50 | 0.718 | 4.428 | 22 | 20 | 8 | 0.878 |
| bounded_blackout | q_learning_blackout | 50 | 48.012 | 9.36 | 49 | 1 | 0 | 9.06e-14 |
| bounded_blackout | neural_q_blackout | 50 | 21.808 | 7.235 | 38 | 12 | 0 | 0.000306 |
| bounded_blackout | am_ppo | 50 | 72.563 | 13.881 | 46 | 4 | 0 | 4.46e-10 |
| bounded_blackout | am_ppo_plus_ls | 50 | 19.576 | 7.254 | 38 | 11 | 1 | 0.000142 |
