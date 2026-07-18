# Uncertainty Robustness - 2026-07-18

Routes are planned on the nominal scenario and evaluated after perturbing wake phase, data amount, protocol rate, setup/reconnect cost, switching cost, and edge loss.

| Uncertainty | Planner | Scenarios | Time mean | Max blackout mean | Max blackout 95% CI | 90s violations | Endurance violations | Planning runtime ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0 | distance_only | 50 | 1584.443 | 170.325 | 12.209 | 50 | 27 | 0.023 |
| 0.0 | protocol_aware | 50 | 1137.341 | 87.326 | 4.883 | 20 | 5 | 327.786 |
| 0.0 | bounded_blackout | 50 | 1099.073 | 65.684 | 3.782 | 1 | 4 | 1942.38 |
| 0.02 | distance_only | 50 | 1593.259 | 175.83 | 12.302 | 50 | 28 | 0.023 |
| 0.02 | protocol_aware | 50 | 1282.297 | 124.849 | 16.163 | 32 | 12 | 327.786 |
| 0.02 | bounded_blackout | 50 | 1236.399 | 102.528 | 17.522 | 16 | 12 | 1942.38 |
| 0.05 | distance_only | 50 | 1588.771 | 173.794 | 12.309 | 50 | 27 | 0.023 |
| 0.05 | protocol_aware | 50 | 1389.688 | 146.423 | 16.864 | 38 | 18 | 327.786 |
| 0.05 | bounded_blackout | 50 | 1362.41 | 137.157 | 19.524 | 30 | 18 | 1942.38 |
| 0.1 | distance_only | 50 | 1584.674 | 176.741 | 12.515 | 49 | 26 | 0.023 |
| 0.1 | protocol_aware | 50 | 1489.288 | 170.356 | 15.803 | 44 | 23 | 327.786 |
| 0.1 | bounded_blackout | 50 | 1448.23 | 162.773 | 19.337 | 37 | 24 | 1942.38 |

Reading: the perturbation is a robustness check for known-profile offline planning, not an online replanning result.
