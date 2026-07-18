# Public-measurement-informed profile rerun - 2026-07-18

This check keeps the scenario generator, node count, seeds, and routers fixed while replacing the reference protocol profile with an envelope informed by public aerial measurements, ground measurements, standards, and the local service-time check.

## Measurement-informed protocol profile

| Protocol | Range | Rate | Setup | Reconnect | Recovery | Cycle/window | Edge loss | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LoRa | 650.0 | 5.5 | 2.0 | 1.5 | 1.0 | 300/12 | 0.18 | public aerial measurement informed |
| ZigBee | 110.0 | 250.0 | 0.7 | 0.8 | 10.0 | 120/15 | 0.14 | public aerial measurement informed |
| BLE | 45.0 | 100.0 | 0.6 | 1.0 | 6.0 | 80/10 | 0.1 | measurement and standard informed |
| WiFi | 100.0 | 1000.0 | 0.6 | 0.8 | 5.0 | 120/30 | 0.06 | bench and standard informed |

## Evidence mapping notes

- LoRa: Real-UAV LoRa/LoRaWAN public measurements for range, edge reliability, and aerial link variability; packet-capture LoRaWAN studies for low-rate and loss envelope.
- ZigBee: Real-UAV 2.4 GHz IEEE 802.15.4 measurements for aerial edge loss and range collapse; XBee/802.15.4 studies for nominal rate and recovery.
- BLE: Real-chipset BLE discovery/reconnect studies and RSSI-distance datasets; no public aerial BLE dataset was used.
- WiFi: K10 Wi-Fi bench measurements for service-time scale plus conservative short-range edge-loss assumptions; no public aerial Wi-Fi IoT dataset was used.

## Main random-suite summary

| Planner | Scenarios | Time mean | Max blackout mean | Max blackout std | 90s violations | Endurance violations | Joint violations | Runtime mean ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bounded_blackout | 50 | 2105.355 | 76.16 | 28.858 | 10 | 38 | 38 | 1956.043 |
| distance_only | 50 | 2710.263 | 213.084 | 58.357 | 49 | 46 | 49 | 0.027 |
| genetic_algorithm | 50 | 2181.895 | 96.465 | 16.002 | 32 | 42 | 46 | 691.09 |
| ordinary_collection | 50 | 2689.483 | 221.72 | 54.387 | 50 | 47 | 50 | 13.979 |
| particle_swarm | 50 | 2175.532 | 93.969 | 18.61 | 30 | 41 | 44 | 232.781 |
| protocol_aware | 50 | 2156.889 | 97.159 | 28.685 | 26 | 40 | 43 | 318.181 |

## Average/freshness-style checks

| Planner | Scenarios | Time mean | Max blackout mean | Mean gap mean | Mean completion mean | 90s violations | Endurance violations | Joint violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| average_gap | 50 | 2175.508 | 91.608 | 36.545 | 1020.859 | 25 | 40 | 42 |
| bounded_beta90 | 50 | 2105.355 | 76.16 | 35.191 | 991.947 | 10 | 38 | 38 |
| freshness_focused | 50 | 2334.23 | 153.979 | 50.826 | 748.923 | 40 | 43 | 49 |
| protocol_aware_time | 50 | 2156.889 | 97.159 | 40.241 | 988.304 | 26 | 40 | 43 |
| soft_penalty_w12 | 50 | 2176.187 | 85.227 | 40.172 | 1038.861 | 15 | 40 | 40 |

Reading: the rerun tests whether the route ordering persists under an externally informed protocol envelope while keeping the evaluator and scenario distribution fixed.
