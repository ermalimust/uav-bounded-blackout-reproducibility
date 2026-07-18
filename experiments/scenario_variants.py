from __future__ import annotations

import random
from dataclasses import replace

from uav_protocol_planning.models import ProtocolProfile, Scenario


def generic_protocol() -> ProtocolProfile:
    return ProtocolProfile(
        name="Generic",
        nominal_range_m=150.0,
        data_rate_kbps=160.0,
        connection_setup_s=0.9,
        reconnect_penalty_s=0.7,
        sleep_cycle_s=60.0,
        awake_window_s=30.0,
        packet_loss_at_edge=0.08,
        switch_penalty_s=0.0,
        recovery_threshold_s=5.0,
    )


def always_awake(scenario: Scenario) -> Scenario:
    protocols = {
        name: replace(profile, sleep_cycle_s=0.0, awake_window_s=0.0)
        for name, profile in scenario.protocols.items()
    }
    return replace(scenario, name=f"{scenario.name}_no_sleep", protocols=protocols)


def without_radio_obstacles(scenario: Scenario) -> Scenario:
    return replace(scenario, name=f"{scenario.name}_no_radio_obstacles", radio_obstacles=())


def homogeneous_protocols(scenario: Scenario) -> Scenario:
    generic = generic_protocol()
    nodes = {
        node_id: replace(node, protocol="Generic")
        for node_id, node in scenario.nodes.items()
    }
    return replace(
        scenario,
        name=f"{scenario.name}_homogeneous_protocols",
        protocols={"Generic": generic},
        nodes=nodes,
        radio_obstacles=(),
    )


def blackout_variant(scenario: Scenario, target_s: float) -> Scenario:
    return replace(scenario, name=f"{scenario.name}_blackout_{int(target_s)}s", max_blackout_s=target_s)


def protocol_ratio_variant(scenario: Scenario, heterogeneity_ratio: float, seed: int = 31) -> Scenario:
    heterogeneity_ratio = max(0.0, min(1.0, heterogeneity_ratio))
    generic = generic_protocol()
    node_ids = list(scenario.nodes)
    random.Random(seed).shuffle(node_ids)
    heterogeneous_count = round(len(node_ids) * heterogeneity_ratio)
    heterogeneous_ids = set(node_ids[:heterogeneous_count])

    nodes = {}
    for node_id, node in scenario.nodes.items():
        if node_id in heterogeneous_ids:
            nodes[node_id] = node
        else:
            nodes[node_id] = replace(node, protocol="Generic")

    protocols = dict(scenario.protocols)
    protocols["Generic"] = generic
    return replace(
        scenario,
        name=f"{scenario.name}_heterogeneity_{heterogeneity_ratio:.2f}",
        protocols=protocols,
        nodes=nodes,
    )
