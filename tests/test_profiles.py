from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_protocol_planning.planners import bounded_blackout_route, protocol_aware_route
from uav_protocol_planning.scenarios import (
    build_public_measurement_informed_protocols,
    build_random_scenario,
)
from uav_protocol_planning.simulation import simulate_route


class MeasurementInformedProfileTests(unittest.TestCase):
    def test_public_measurement_profile_values(self) -> None:
        profiles = build_public_measurement_informed_protocols()

        self.assertEqual(set(profiles), {"LoRa", "ZigBee", "BLE", "WiFi"})
        self.assertAlmostEqual(profiles["LoRa"].nominal_range_m, 650.0)
        self.assertAlmostEqual(profiles["LoRa"].packet_loss_at_edge, 0.18)
        self.assertAlmostEqual(profiles["ZigBee"].nominal_range_m, 110.0)
        self.assertAlmostEqual(profiles["ZigBee"].packet_loss_at_edge, 0.14)

    def test_public_measurement_route_evaluation_runs(self) -> None:
        scenario = build_random_scenario(
            seed=101,
            node_count=14,
            profile_variant="public_measurement_informed",
        )

        for route in (
            protocol_aware_route(scenario),
            bounded_blackout_route(scenario, budget=90.0),
        ):
            result = simulate_route(scenario, route)
            self.assertEqual(set(route), set(scenario.nodes))
            self.assertGreater(result.total_time_s, 0.0)
            self.assertGreater(result.max_blackout_s, 0.0)


if __name__ == "__main__":
    unittest.main()
