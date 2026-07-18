# Wake-Phase Perturbation Study - 2026-07-18

Routes are planned on nominal wake phases and evaluated after shifting each node phase by a uniformly sampled error in [-Delta, Delta]. Only wake phase is perturbed; protocol rates, setup/reconnect costs, packet loss, and data amounts remain nominal.

| Delta (s) | Planner | Scenarios | Time mean | Max blackout mean | Max blackout 95% CI | 90s violations | Endurance violations | Joint violations | Planning runtime ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0 | distance_only | 50 | 1582.145 | 171.268 | 11.923 | 49 | 26 | 49 | 0.023 |
| 0.0 | protocol_aware | 50 | 1128.508 | 87.793 | 5.525 | 25 | 3 | 26 | 316.089 |
| 0.0 | bounded_blackout | 50 | 1095.555 | 63.245 | 3.51 | 2 | 2 | 2 | 1886.055 |
| 2.0 | distance_only | 50 | 1576.666 | 171.122 | 11.944 | 49 | 25 | 49 | 0.023 |
| 2.0 | protocol_aware | 50 | 1192.474 | 102.221 | 10.412 | 32 | 5 | 32 | 316.089 |
| 2.0 | bounded_blackout | 50 | 1173.022 | 91.847 | 15.566 | 16 | 6 | 16 | 1886.055 |
| 5.0 | distance_only | 50 | 1569.536 | 172.242 | 11.492 | 49 | 24 | 49 | 0.023 |
| 5.0 | protocol_aware | 50 | 1289.342 | 128.928 | 16.693 | 35 | 9 | 36 | 316.089 |
| 5.0 | bounded_blackout | 50 | 1220.819 | 104.728 | 16.673 | 21 | 6 | 21 | 1886.055 |
| 10.0 | distance_only | 50 | 1565.572 | 175.641 | 11.608 | 49 | 27 | 49 | 0.023 |
| 10.0 | protocol_aware | 50 | 1327.158 | 138.688 | 16.338 | 36 | 15 | 37 | 316.089 |
| 10.0 | bounded_blackout | 50 | 1362.721 | 141.361 | 18.347 | 35 | 16 | 35 | 1886.055 |
| 20.0 | distance_only | 50 | 1594.019 | 178.829 | 9.85 | 50 | 24 | 50 | 0.023 |
| 20.0 | protocol_aware | 50 | 1449.508 | 163.744 | 14.362 | 48 | 19 | 49 | 316.089 |
| 20.0 | bounded_blackout | 50 | 1476.747 | 164.881 | 14.172 | 47 | 19 | 47 | 1886.055 |
| 30.0 | distance_only | 50 | 1591.001 | 170.015 | 12.387 | 49 | 29 | 49 | 0.023 |
| 30.0 | protocol_aware | 50 | 1543.432 | 172.765 | 13.778 | 49 | 28 | 49 | 316.089 |
| 30.0 | bounded_blackout | 50 | 1539.662 | 175.013 | 14.216 | 48 | 26 | 48 | 1886.055 |

Reading: this isolates the reviewer-requested phase-error effect. It does not claim online replanning; it bounds the known-profile assumption under offline planning.
