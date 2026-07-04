# Public measurement-trace calibrated profile rerun - 2026-07-04

This check keeps the scenario generator, node count, seeds, and routers fixed, but replaces the reference protocol profile with a public measurement-trace calibrated profile. It is not a closed-loop UAV deployment experiment. Public real-UAV traces are used for the LoRa and ZigBee-class radio envelope; BLE and WiFi fields remain grounded in ground/bench measurements and standards.

## Calibrated protocol profile

| Protocol | Range | Rate | Setup | Reconnect | Disc. | Cycle/window | Edge loss | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LoRa | 650.0 | 5.5 | 2.0 | 1.5 | 1.0 | 300/12 | 0.18 | public real-UAV trace calibrated |
| ZigBee | 110.0 | 250.0 | 0.7 | 0.8 | 10.0 | 120/15 | 0.14 | public real-UAV trace calibrated |
| BLE | 45.0 | 100.0 | 0.6 | 1.0 | 6.0 | 80/10 | 0.1 | ground measurement / standard derived |
| WiFi | 100.0 | 1000.0 | 0.6 | 0.8 | 5.0 | 120/30 | 0.06 | local bench / standard derived |

## Calibration notes

- LoRa: Real-UAV LoRa/LoRaWAN public measurements for range, edge reliability, and aerial link variability; packet-capture LoRaWAN studies for low-rate and loss envelope.
- ZigBee: Real-UAV 2.4 GHz IEEE 802.15.4 measurements for aerial edge loss and range collapse; XBee/802.15.4 studies for nominal rate and recovery.
- BLE: Real-chipset BLE discovery/reconnect studies and RSSI-distance datasets; no public aerial BLE dataset was used.
- WiFi: K10 Wi-Fi bench measurements for service-time scale plus conservative short-range edge-loss assumptions; no public aerial Wi-Fi IoT dataset was used.

## Main random-suite summary

| Planner | Scenarios | Time mean | Max blackout mean | Max blackout std | 90s violations | Runtime mean ms |
| --- | --- | --- | --- | --- | --- | --- |
| bounded_blackout | 50 | 2316.065 | 77.95 | 13.618 | 8 | 980.038 |
| distance_only | 50 | 2765.613 | 220.563 | 59.021 | 50 | 0.04 |
| genetic_algorithm | 50 | 2373.678 | 103.859 | 15.366 | 41 | 754.379 |
| ordinary_collection | 50 | 2730.16 | 226.05 | 67.459 | 49 | 26.171 |
| particle_swarm | 50 | 2348.896 | 101.172 | 14.058 | 39 | 248.208 |
| protocol_aware | 50 | 2306.119 | 112.276 | 32.029 | 37 | 265.157 |

## Average/freshness-style checks

| Planner | Scenarios | Time mean | Max blackout mean | Mean gap mean | Mean completion mean | 90s violations |
| --- | --- | --- | --- | --- | --- | --- |
| average_gap | 50 | 2286.885 | 103.081 | 47.736 | 1153.561 | 34 |
| bounded_beta90 | 50 | 2311.273 | 78.609 | 49.362 | 1149.734 | 8 |
| freshness_focused | 50 | 2532.163 | 198.257 | 64.088 | 799.304 | 48 |
| protocol_aware_time | 50 | 2306.119 | 112.276 | 49.018 | 1076.724 | 37 |
| soft_penalty_w12 | 50 | 2393.658 | 89.153 | 54.854 | 1172.36 | 21 |

Reading: this check should be interpreted as public measurement-trace calibration of scheduler inputs, not as closed-loop real-UAV validation of the route controller.
