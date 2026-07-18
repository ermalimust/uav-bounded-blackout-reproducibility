# Literature-aligned profile robustness - 2026-07-18

This robustness check keeps the scenario generator, node count, seeds, and routers fixed, but replaces the reference protocol profile with a conservative literature-aligned variant. It is an alternate parameter envelope based on non-MDPI protocol studies and standards, not a fitted target-system model.

## Literature-aligned protocol profile

| Protocol | Range | Rate | Setup | Reconnect | Cycle/window | Edge loss | Switch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LoRa | 600.0 | 5.5 | 2.0 | 1.5 | 300/12 | 0.16 | 2.2 |
| ZigBee | 120.0 | 250.0 | 0.7 | 0.8 | 120/15 | 0.1 | 1.4 |
| BLE | 45.0 | 100.0 | 1.0 | 1.0 | 80/10 | 0.08 | 1.5 |
| WiFi | 100.0 | 2000.0 | 0.6 | 0.8 | 120/30 | 0.06 | 1.2 |

## Main random-suite summary

| Planner | Scenarios | Time mean | Max blackout mean | Max blackout std | 90s violations | Endurance violations | Joint violations | Runtime mean ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bounded_blackout | 50 | 2101.018 | 81.475 | 24.95 | 17 | 39 | 39 | 1887.166 |
| distance_only | 50 | 2691.3 | 213.048 | 61.44 | 49 | 46 | 49 | 0.027 |
| genetic_algorithm | 50 | 2147.701 | 96.507 | 19.313 | 30 | 40 | 43 | 694.4 |
| ordinary_collection | 50 | 2690.515 | 221.446 | 53.377 | 50 | 47 | 50 | 13.01 |
| particle_swarm | 50 | 2159.602 | 100.129 | 19.646 | 37 | 41 | 45 | 230.39 |
| protocol_aware | 50 | 2144.784 | 98.212 | 22.471 | 31 | 39 | 43 | 311.921 |

## Average/freshness-style checks

| Planner | Scenarios | Time mean | Max blackout mean | Mean gap mean | Mean completion mean | 90s violations | Endurance violations | Joint violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| average_gap | 50 | 2146.403 | 93.375 | 35.928 | 1078.15 | 19 | 39 | 41 |
| bounded_beta90 | 50 | 2101.018 | 81.475 | 36.238 | 1025.985 | 17 | 39 | 39 |
| freshness_focused | 50 | 2303.962 | 159.956 | 50.083 | 726.726 | 45 | 42 | 48 |
| protocol_aware_time | 50 | 2144.784 | 98.212 | 40.002 | 1004.033 | 31 | 39 | 43 |
| soft_penalty_w12 | 50 | 2153.153 | 89.033 | 40.138 | 1030.232 | 17 | 40 | 40 |

Reading: the conclusion is robust if the bounded-blackout route remains the lowest maximum-blackout option and the average/freshness alternatives continue to leave blackout-budget violations.
