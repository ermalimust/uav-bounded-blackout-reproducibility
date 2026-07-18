from __future__ import annotations

from pathlib import Path
import sys
import unittest
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_protocol_planning.planners import (
    action_masked_ppo_route,
    average_gap_route,
    distance_only_route,
    freshness_focused_route,
    genetic_algorithm_blackout_route,
    genetic_algorithm_route,
    neural_q_blackout_route,
    ordinary_data_collection_route,
    particle_swarm_blackout_route,
    particle_swarm_route,
    protocol_aware_route,
    q_learning_blackout_route,
    soft_blackout_penalty_route,
)
from uav_protocol_planning.models import IoTNode, ProtocolProfile, Scenario
from uav_protocol_planning.scenarios import build_reference_scenario
from uav_protocol_planning.simulation import simulate_route, wait_until_awake


class SimulationTests(unittest.TestCase):
    def test_routes_visit_every_node_once(self) -> None:
        scenario = build_reference_scenario()

        for route in (
            distance_only_route(scenario),
            protocol_aware_route(scenario),
            protocol_aware_route(scenario, blackout_weight=12.0),
            soft_blackout_penalty_route(scenario),
            average_gap_route(scenario, max_passes=4),
            freshness_focused_route(scenario, max_passes=4),
            genetic_algorithm_route(scenario),
            genetic_algorithm_blackout_route(scenario, population_size=8, generations=8),
            ordinary_data_collection_route(scenario),
            particle_swarm_route(scenario, swarm_size=8, iterations=8),
            particle_swarm_blackout_route(scenario, swarm_size=8, iterations=8),
            q_learning_blackout_route(scenario, episodes=12),
            neural_q_blackout_route(scenario, episodes=4, hidden_size=8, batch_size=4),
            action_masked_ppo_route(scenario, episodes=4, hidden_size=8, update_epochs=1),
        ):
            self.assertEqual(len(route), len(scenario.nodes))
            self.assertEqual(set(route), set(scenario.nodes))

    def test_simulation_metrics_are_positive(self) -> None:
        scenario = build_reference_scenario()
        result = simulate_route(scenario, protocol_aware_route(scenario))

        self.assertGreater(result.total_time_s, 0.0)
        self.assertGreater(result.flight_distance_m, 0.0)
        self.assertGreaterEqual(result.data_success_rate, 0.0)
        self.assertLessEqual(result.data_success_rate, 1.0)
        self.assertEqual(len(result.collected_nodes), len(scenario.nodes))
        self.assertIsInstance(result.mission_feasible, bool)

    def test_nominal_range_changes_contact_point_and_mission_time(self) -> None:
        short_range = ProtocolProfile(
            name="Radio",
            nominal_range_m=10.0,
            data_rate_kbps=1000.0,
            connection_setup_s=0.0,
            reconnect_penalty_s=0.0,
            sleep_cycle_s=0.0,
            awake_window_s=0.0,
            packet_loss_at_edge=0.0,
            switch_penalty_s=0.0,
            recovery_threshold_s=1000.0,
        )
        long_range = replace(short_range, nominal_range_m=50.0)

        def make_scenario(profile: ProtocolProfile) -> Scenario:
            return Scenario(
                name="range_contact_test",
                width_m=120.0,
                height_m=20.0,
                start=(0.0, 0.0),
                speed_mps=1.0,
                protocols={"Radio": profile},
                nodes={"N": IoTNode("N", 100.0, 0.0, "Radio", data_kb=0.0)},
                radio_obstacles=(),
            )

        short_result = simulate_route(make_scenario(short_range), ("N",))
        long_result = simulate_route(make_scenario(long_range), ("N",))

        self.assertGreater(short_result.flight_distance_m, long_result.flight_distance_m)
        self.assertGreater(short_result.total_time_s, long_result.total_time_s)
        self.assertEqual(short_result.event_log[0]["effective_range_m"], 10.0)
        self.assertEqual(long_result.event_log[0]["effective_range_m"], 50.0)

    def test_wait_until_awake_respects_sleep_cycle(self) -> None:
        scenario = build_reference_scenario()
        node = scenario.nodes["N02"]

        self.assertEqual(wait_until_awake(12.0, node, scenario), 0.0)
        self.assertGreater(wait_until_awake(40.0, node, scenario), 0.0)

    def test_reconnect_uses_protocol_specific_threshold(self) -> None:
        wifi = ProtocolProfile(
            name="WiFi",
            nominal_range_m=0.1,
            data_rate_kbps=1000.0,
            connection_setup_s=0.0,
            reconnect_penalty_s=7.0,
            sleep_cycle_s=0.0,
            awake_window_s=0.0,
            packet_loss_at_edge=0.0,
            switch_penalty_s=0.0,
            recovery_threshold_s=4.0,
        )
        lora = replace(wifi, name="LoRa", data_rate_kbps=20.0, recovery_threshold_s=1.0)
        scenario = Scenario(
            name="protocol_specific_recovery_test",
            width_m=50.0,
            height_m=10.0,
            start=(0.0, 0.0),
            speed_mps=1.0,
            protocols={"WiFi": wifi, "LoRa": lora},
            nodes={
                "W1": IoTNode("W1", 1.0, 0.0, "WiFi", data_kb=0.0),
                "L": IoTNode("L", 4.0, 0.0, "LoRa", data_kb=0.0),
                "W2": IoTNode("W2", 7.0, 0.0, "WiFi", data_kb=0.0),
            },
            radio_obstacles=(),
        )

        result = simulate_route(scenario, ("W1", "L", "W2"))

        # W2 is reached less than 4 s after the intervening LoRa contact but
        # more than 4 s after the previous Wi-Fi activity.  A single global
        # activity clock would therefore miss this recovery event.
        self.assertEqual(result.reconnect_count, 2)
        self.assertFalse(result.event_log[0]["reconnected"])
        self.assertTrue(result.event_log[1]["reconnected"])
        self.assertTrue(result.event_log[2]["reconnected"])
        self.assertEqual(result.event_log[0]["recovery_threshold_s"], 4.0)
        self.assertEqual(result.event_log[1]["recovery_threshold_s"], 1.0)


if __name__ == "__main__":
    unittest.main()
