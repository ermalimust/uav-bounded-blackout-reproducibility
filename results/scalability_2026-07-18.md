# Scalability Study - 2026-07-18

Each row averages 3 random heterogeneous scenario(s). The budget is 90 s.
`seed_only` uses no local-search passes and isolates large-n runtime of the seed/candidate-pool construction; `capped_6_passes` uses six deterministic first-improvement passes and is reported for 25 and 50 nodes.

| Mode | Nodes | Planner | Scenarios | Time mean | Distance mean | Max blackout mean | 90s violations | Endurance violations | Runtime mean ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seed_only | 25 | distance_only | 3 | 2574.722 | 3061.394 | 192.274 | 3 | 3 | 0.067 |
| seed_only | 25 | protocol_aware | 3 | 1872.699 | 3857.253 | 112.277 | 2 | 3 | 3.197 |
| seed_only | 25 | bounded_blackout | 3 | 1771.445 | 3934.659 | 100.586 | 2 | 2 | 19.301 |
| seed_only | 50 | distance_only | 3 | 5563.246 | 3872.573 | 213.772 | 3 | 3 | 0.205 |
| seed_only | 50 | protocol_aware | 3 | 3995.029 | 6091.183 | 137.34 | 3 | 3 | 9.356 |
| seed_only | 50 | bounded_blackout | 3 | 3511.045 | 5816.772 | 119.54 | 3 | 3 | 61.613 |
| seed_only | 100 | distance_only | 3 | 10045.678 | 4960.081 | 222.318 | 3 | 3 | 0.786 |
| seed_only | 100 | protocol_aware | 3 | 7184.288 | 8557.452 | 142.928 | 3 | 3 | 31.417 |
| seed_only | 100 | bounded_blackout | 3 | 6500.571 | 8306.622 | 110.428 | 2 | 3 | 202.206 |
| seed_only | 200 | distance_only | 3 | 20074.694 | 6240.87 | 227.663 | 3 | 3 | 3.109 |
| seed_only | 200 | protocol_aware | 3 | 14004.233 | 11661.641 | 135.338 | 3 | 3 | 119.177 |
| seed_only | 200 | bounded_blackout | 3 | 13987.545 | 11662.625 | 127.05 | 3 | 3 | 740.531 |
| capped_6_passes | 25 | distance_only | 3 | 2574.722 | 3061.394 | 192.274 | 3 | 3 | 0.059 |
| capped_6_passes | 25 | protocol_aware | 3 | 1832.531 | 4435.367 | 115.9 | 2 | 3 | 426.399 |
| capped_6_passes | 25 | bounded_blackout | 3 | 1636.299 | 4012.718 | 67.66 | 0 | 1 | 3007.72 |
| capped_6_passes | 50 | distance_only | 3 | 5563.246 | 3872.573 | 213.772 | 3 | 3 | 0.208 |
| capped_6_passes | 50 | protocol_aware | 3 | 3983.631 | 6846.739 | 133.504 | 3 | 3 | 8352.892 |
| capped_6_passes | 50 | bounded_blackout | 3 | 3500.62 | 6232.796 | 85.179 | 1 | 3 | 44866.113 |

Reading: this is an implementation-level scaling check, not a hardware-independent complexity claim.
