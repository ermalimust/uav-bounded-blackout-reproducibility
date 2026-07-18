# Ablation Study Result - 2026-07-18

| Scenario | Planner | Time (s) | Distance (m) | Success | Max blackout (s) | Reconnects | Switches | Radio hits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference | distance_only | 2126.934 | 2906.071 | 1.0 | 203.015 | 13 | 13 | 3 |
| reference | ordinary_collection | 1609.248 | 2926.059 | 1.0 | 114.121 | 14 | 13 | 3 |
| reference | protocol_aware | 1371.245 | 3147.929 | 1.0 | 87.981 | 14 | 12 | 3 |
| reference | bounded_blackout | 1357.891 | 3023.825 | 1.0 | 56.461 | 14 | 13 | 3 |
| reference | genetic_algorithm | 1312.309 | 4328.894 | 1.0 | 70.683 | 14 | 13 | 3 |
| reference | particle_swarm | 1482.079 | 3678.869 | 1.0 | 96.0 | 14 | 12 | 3 |
| homogeneous_protocols | distance_only | 599.59 | 2820.345 | 1.0 | 66.948 | 12 | 0 | 0 |
| homogeneous_protocols | ordinary_collection | 577.961 | 2582.98 | 1.0 | 51.987 | 12 | 0 | 0 |
| homogeneous_protocols | protocol_aware | 465.526 | 2576.425 | 1.0 | 38.956 | 8 | 0 | 0 |
| homogeneous_protocols | bounded_blackout | 465.526 | 2576.425 | 1.0 | 38.956 | 8 | 0 | 0 |
| homogeneous_protocols | genetic_algorithm | 465.526 | 2576.425 | 1.0 | 38.956 | 8 | 0 | 0 |
| homogeneous_protocols | particle_swarm | 462.336 | 2520.969 | 1.0 | 39.018 | 8 | 0 | 0 |
| no_sleep | distance_only | 1081.579 | 2906.071 | 1.0 | 72.429 | 13 | 13 | 3 |
| no_sleep | ordinary_collection | 1112.06 | 2926.059 | 1.0 | 47.797 | 14 | 13 | 3 |
| no_sleep | protocol_aware | 1034.741 | 2737.53 | 1.0 | 70.359 | 13 | 12 | 3 |
| no_sleep | bounded_blackout | 1034.741 | 2737.53 | 1.0 | 70.359 | 13 | 12 | 3 |
| no_sleep | genetic_algorithm | 1034.741 | 2737.53 | 1.0 | 70.359 | 13 | 12 | 3 |
| no_sleep | particle_swarm | 1034.741 | 2737.53 | 1.0 | 70.359 | 13 | 12 | 3 |
| no_radio_obstacles | distance_only | 1886.935 | 2875.121 | 1.0 | 187.67 | 13 | 13 | 0 |
| no_radio_obstacles | ordinary_collection | 1321.26 | 2889.448 | 1.0 | 113.368 | 14 | 13 | 0 |
| no_radio_obstacles | protocol_aware | 1176.116 | 3583.707 | 1.0 | 114.245 | 14 | 13 | 0 |
| no_radio_obstacles | bounded_blackout | 1148.459 | 3999.982 | 1.0 | 58.415 | 14 | 13 | 0 |
| no_radio_obstacles | genetic_algorithm | 1098.234 | 3285.756 | 1.0 | 87.047 | 14 | 11 | 0 |
| no_radio_obstacles | particle_swarm | 1176.442 | 2976.798 | 1.0 | 91.823 | 14 | 13 | 0 |
| blackout_45s | distance_only | 2126.934 | 2906.071 | 1.0 | 203.015 | 13 | 13 | 3 |
| blackout_45s | ordinary_collection | 1609.248 | 2926.059 | 1.0 | 114.121 | 14 | 13 | 3 |
| blackout_45s | protocol_aware | 1322.46 | 3198.589 | 1.0 | 89.669 | 14 | 12 | 3 |
| blackout_45s | bounded_blackout | 1431.218 | 4044.284 | 1.0 | 60.988 | 14 | 13 | 3 |
| blackout_45s | genetic_algorithm | 1431.218 | 4044.284 | 1.0 | 60.988 | 14 | 13 | 3 |
| blackout_45s | particle_swarm | 1431.218 | 4044.284 | 1.0 | 60.988 | 14 | 13 | 3 |
| blackout_60s | distance_only | 2126.934 | 2906.071 | 1.0 | 203.015 | 13 | 13 | 3 |
| blackout_60s | ordinary_collection | 1609.248 | 2926.059 | 1.0 | 114.121 | 14 | 13 | 3 |
| blackout_60s | protocol_aware | 1376.455 | 3154.998 | 1.0 | 69.365 | 14 | 12 | 3 |
| blackout_60s | bounded_blackout | 1431.218 | 4044.284 | 1.0 | 60.988 | 14 | 13 | 3 |
| blackout_60s | genetic_algorithm | 1373.937 | 4727.855 | 1.0 | 62.5 | 14 | 13 | 3 |
| blackout_60s | particle_swarm | 1422.425 | 4659.011 | 1.0 | 62.5 | 14 | 12 | 3 |
| blackout_75s | distance_only | 2126.934 | 2906.071 | 1.0 | 203.015 | 13 | 13 | 3 |
| blackout_75s | ordinary_collection | 1609.248 | 2926.059 | 1.0 | 114.121 | 14 | 13 | 3 |
| blackout_75s | protocol_aware | 1376.455 | 3154.998 | 1.0 | 69.365 | 14 | 12 | 3 |
| blackout_75s | bounded_blackout | 1322.255 | 3847.587 | 1.0 | 61.329 | 14 | 10 | 3 |
| blackout_75s | genetic_algorithm | 1373.49 | 4856.761 | 1.0 | 64.718 | 14 | 13 | 3 |
| blackout_75s | particle_swarm | 1436.962 | 4271.761 | 1.0 | 74.015 | 14 | 12 | 3 |
| blackout_120s | distance_only | 2126.934 | 2906.071 | 1.0 | 203.015 | 13 | 13 | 3 |
| blackout_120s | ordinary_collection | 1609.248 | 2926.059 | 1.0 | 114.121 | 14 | 13 | 3 |
| blackout_120s | protocol_aware | 1371.245 | 3147.929 | 1.0 | 87.981 | 14 | 12 | 3 |
| blackout_120s | bounded_blackout | 1357.891 | 3023.825 | 1.0 | 56.461 | 14 | 13 | 3 |
| blackout_120s | genetic_algorithm | 1312.309 | 4328.894 | 1.0 | 70.683 | 14 | 13 | 3 |
| blackout_120s | particle_swarm | 1482.079 | 3678.869 | 1.0 | 96.0 | 14 | 12 | 3 |

## Reading Notes

- `homogeneous_protocols` removes protocol differences to test whether the claimed benefit depends on heterogeneity.
- `no_sleep` isolates intermittent connectivity.
- `no_radio_obstacles` isolates protocol-specific invisible obstacles.
- `blackout_*s` variants test whether a stricter maximum blackout target changes route selection.
