# Task-driven gap checks - 2026-07-18

These checks add three reviewer-facing pieces of evidence: a small K10 WiFi reality check, a fixed soft-blackout-penalty baseline, and average/freshness-style metric baselines.

## 1. K10 WiFi sanity evidence

| Source | Requests | Successes | Success rate (%) | Mean latency (ms) | Min latency (ms) | Max latency (ms) |
| --- | --- | --- | --- | --- | --- | --- |
| k10_latency_log_20260528_231959.csv | 60 | 60 | 100.0 | 190.9 | 40.9 | 355.5 |
| k10_latency_log_20260528_232159.csv | 300 | 300 | 100.0 | 197.0 | 39.7 | 358.8 |
| k10_distance_test_20260528_233257_raw.csv | 30 | 30 | 100.0 | 208.2 | 67.1 | 341.1 |
| combined_k10_wifi_http | 390 | 390 | 100.0 | 197.0 | 39.7 | 358.8 |

Interpretation: these logs only support a minimal WiFi sanity check for K10-as-node operation. They do not yet measure RSSI, distance curves, BLE/LoRa, or true reconnect delay.

## 2. Soft penalty and average/freshness baselines

Random-suite summary over 50 heterogeneous scenarios. The budget column counts how often a route exceeds a 90 s maximum-blackout target.

| Planner | Scenarios | Time mean | Max blackout mean | Mean gap mean | Mean completion mean | 90s violations | Endurance violations | Joint violations | Runtime ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| distance_only | 50 | 1563.68 | 162.352 | 64.715 | 816.969 | 47 | 26 | 47 | 0.026 |
| ordinary_collection | 50 | 1544.249 | 169.963 | 63.27 | 824.147 | 48 | 27 | 48 | 13.821 |
| protocol_aware_time | 50 | 1133.389 | 89.236 | 35.592 | 560.353 | 22 | 2 | 23 | 287.099 |
| soft_penalty_w12 | 50 | 1150.041 | 76.487 | 36.559 | 574.678 | 0 | 2 | 2 | 314.794 |
| average_gap | 50 | 1118.591 | 85.316 | 33.733 | 577.943 | 16 | 2 | 18 | 775.31 |
| freshness_focused | 50 | 1210.372 | 115.239 | 40.727 | 469.513 | 32 | 5 | 33 | 800.807 |
| bounded_beta90 | 50 | 1084.915 | 63.808 | 31.95 | 542.494 | 1 | 2 | 2 | 1763.133 |

Interpretation: the fixed soft penalty and averaged timing objectives are useful comparators, but they do not expose a hard operating guarantee. The constrained bounded-blackout router is the only baseline here that directly targets a specified maximum-blackout budget.
