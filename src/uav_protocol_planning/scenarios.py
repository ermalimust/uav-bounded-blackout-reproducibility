from __future__ import annotations

import random

from .models import IoTNode, ProtocolProfile, RadioObstacle, Scenario


def build_default_protocols() -> dict[str, ProtocolProfile]:
    # Sleep cycles and awake windows recalibrated to a more realistic duty-cycled
    # regime (cycles x2, windows x0.6) so that maximum blackout depends on the
    # visiting order, decoupling it from pure travel time.
    return {
        "LoRa": ProtocolProfile(
            name="LoRa",
            nominal_range_m=450.0,
            data_rate_kbps=18.0,
            connection_setup_s=1.5,
            reconnect_penalty_s=1.0,
            sleep_cycle_s=240.0,
            awake_window_s=14.4,
            packet_loss_at_edge=0.12,
            switch_penalty_s=2.0,
            disconnect_threshold_s=1.0,
        ),
        "ZigBee": ProtocolProfile(
            name="ZigBee",
            nominal_range_m=90.0,
            data_rate_kbps=80.0,
            connection_setup_s=0.6,
            reconnect_penalty_s=0.7,
            sleep_cycle_s=96.0,
            awake_window_s=12.0,
            packet_loss_at_edge=0.08,
            switch_penalty_s=1.4,
            disconnect_threshold_s=7.5,
        ),
        "BLE": ProtocolProfile(
            name="BLE",
            nominal_range_m=65.0,
            data_rate_kbps=120.0,
            connection_setup_s=1.2,
            reconnect_penalty_s=0.8,
            sleep_cycle_s=72.0,
            awake_window_s=9.6,
            packet_loss_at_edge=0.07,
            switch_penalty_s=1.6,
            disconnect_threshold_s=6.0,
        ),
        "WiFi": ProtocolProfile(
            name="WiFi",
            nominal_range_m=120.0,
            data_rate_kbps=1000.0,
            connection_setup_s=0.8,
            reconnect_penalty_s=0.5,
            sleep_cycle_s=120.0,
            awake_window_s=25.2,
            packet_loss_at_edge=0.05,
            switch_penalty_s=1.2,
            disconnect_threshold_s=5.0,
        ),
    }


def build_literature_aligned_protocols() -> dict[str, ProtocolProfile]:
    """Alternative profile used only for robustness checks.

    These values form a conservative, literature-aligned envelope rather than a
    hardware calibration. The profile keeps LoRa long-range but low-rate, uses a
    nominal IEEE 802.15.4/ZigBee data-rate scale, keeps BLE short-range and
    connection-sensitive, and keeps WiFi high-rate but range-limited.
    """
    return {
        "LoRa": ProtocolProfile(
            name="LoRa",
            nominal_range_m=600.0,
            data_rate_kbps=5.5,
            connection_setup_s=2.0,
            reconnect_penalty_s=1.5,
            sleep_cycle_s=300.0,
            awake_window_s=12.0,
            packet_loss_at_edge=0.16,
            switch_penalty_s=2.2,
            disconnect_threshold_s=1.0,
        ),
        "ZigBee": ProtocolProfile(
            name="ZigBee",
            nominal_range_m=120.0,
            data_rate_kbps=250.0,
            connection_setup_s=0.7,
            reconnect_penalty_s=0.8,
            sleep_cycle_s=120.0,
            awake_window_s=15.0,
            packet_loss_at_edge=0.10,
            switch_penalty_s=1.4,
            disconnect_threshold_s=10.0,
        ),
        "BLE": ProtocolProfile(
            name="BLE",
            nominal_range_m=45.0,
            data_rate_kbps=100.0,
            connection_setup_s=1.0,
            reconnect_penalty_s=1.0,
            sleep_cycle_s=80.0,
            awake_window_s=10.0,
            packet_loss_at_edge=0.08,
            switch_penalty_s=1.5,
            disconnect_threshold_s=6.0,
        ),
        "WiFi": ProtocolProfile(
            name="WiFi",
            nominal_range_m=100.0,
            data_rate_kbps=2000.0,
            connection_setup_s=0.6,
            reconnect_penalty_s=0.8,
            sleep_cycle_s=120.0,
            awake_window_s=30.0,
            packet_loss_at_edge=0.06,
            switch_penalty_s=1.2,
            disconnect_threshold_s=5.0,
        ),
    }


def build_public_trace_calibrated_protocols() -> dict[str, ProtocolProfile]:
    """Profile used for the public measurement-trace calibration rerun.

    This is not a closed-loop UAV deployment profile. It keeps the scheduler
    interface unchanged while replacing the reference envelope with values
    grounded in public measurement traces and measurement papers: LoRa and
    ZigBee-class edge/range terms use real UAV air-to-ground evidence, BLE uses
    real-chipset discovery/reconnect timing evidence, and WiFi keeps the K10
    service-time anchor plus conservative short-range loss assumptions.
    """
    return {
        "LoRa": ProtocolProfile(
            name="LoRa",
            nominal_range_m=650.0,
            data_rate_kbps=5.5,
            connection_setup_s=2.0,
            reconnect_penalty_s=1.5,
            sleep_cycle_s=300.0,
            awake_window_s=12.0,
            packet_loss_at_edge=0.18,
            switch_penalty_s=2.2,
            disconnect_threshold_s=1.0,
        ),
        "ZigBee": ProtocolProfile(
            name="ZigBee",
            nominal_range_m=110.0,
            data_rate_kbps=250.0,
            connection_setup_s=0.7,
            reconnect_penalty_s=0.8,
            sleep_cycle_s=120.0,
            awake_window_s=15.0,
            packet_loss_at_edge=0.14,
            switch_penalty_s=1.4,
            disconnect_threshold_s=10.0,
        ),
        "BLE": ProtocolProfile(
            name="BLE",
            nominal_range_m=45.0,
            data_rate_kbps=100.0,
            connection_setup_s=0.6,
            reconnect_penalty_s=1.0,
            sleep_cycle_s=80.0,
            awake_window_s=10.0,
            packet_loss_at_edge=0.10,
            switch_penalty_s=1.5,
            disconnect_threshold_s=6.0,
        ),
        "WiFi": ProtocolProfile(
            name="WiFi",
            nominal_range_m=100.0,
            data_rate_kbps=1000.0,
            connection_setup_s=0.6,
            reconnect_penalty_s=0.8,
            sleep_cycle_s=120.0,
            awake_window_s=30.0,
            packet_loss_at_edge=0.06,
            switch_penalty_s=1.2,
            disconnect_threshold_s=5.0,
        ),
    }


def _select_protocols(profile_variant: str) -> dict[str, ProtocolProfile]:
    if profile_variant == "reference":
        return build_default_protocols()
    if profile_variant == "literature_aligned":
        return build_literature_aligned_protocols()
    if profile_variant == "public_trace_calibrated":
        return build_public_trace_calibrated_protocols()
    raise ValueError(f"Unknown protocol profile variant: {profile_variant}")


def build_reference_scenario(profile_variant: str = "reference") -> Scenario:
    protocols = _select_protocols(profile_variant)

    nodes = {
        "N01": IoTNode("N01", 120.0, 160.0, "BLE", 80.0, first_awake_s=0.0),
        "N02": IoTNode("N02", 220.0, 280.0, "ZigBee", 120.0, first_awake_s=10.0),
        "N03": IoTNode("N03", 420.0, 180.0, "WiFi", 850.0, first_awake_s=5.0),
        "N04": IoTNode("N04", 560.0, 260.0, "LoRa", 240.0, first_awake_s=20.0),
        "N05": IoTNode("N05", 680.0, 420.0, "BLE", 90.0, first_awake_s=8.0),
        "N06": IoTNode("N06", 520.0, 520.0, "ZigBee", 150.0, first_awake_s=15.0),
        "N07": IoTNode("N07", 330.0, 610.0, "WiFi", 900.0, first_awake_s=0.0),
        "N08": IoTNode("N08", 180.0, 760.0, "LoRa", 260.0, first_awake_s=45.0),
        "N09": IoTNode("N09", 760.0, 720.0, "LoRa", 300.0, first_awake_s=60.0),
        "N10": IoTNode("N10", 850.0, 540.0, "WiFi", 700.0, first_awake_s=18.0),
        "N11": IoTNode("N11", 910.0, 220.0, "BLE", 110.0, first_awake_s=12.0),
        "N12": IoTNode("N12", 640.0, 850.0, "ZigBee", 130.0, first_awake_s=4.0),
        "N13": IoTNode("N13", 420.0, 860.0, "BLE", 70.0, first_awake_s=22.0),
        "N14": IoTNode("N14", 780.0, 120.0, "LoRa", 220.0, first_awake_s=30.0),
    }

    radio_obstacles = (
        RadioObstacle(
            name="2.4GHz interference zone",
            x_m=540.0,
            y_m=500.0,
            radius_m=180.0,
            affected_protocols=("WiFi", "ZigBee", "BLE"),
            range_multiplier=0.55,
            data_rate_multiplier=0.45,
            loss_addition=0.22,
        ),
        RadioObstacle(
            name="LPWAN shadow zone",
            x_m=780.0,
            y_m=740.0,
            radius_m=155.0,
            affected_protocols=("LoRa",),
            range_multiplier=0.65,
            data_rate_multiplier=0.55,
            loss_addition=0.18,
        ),
    )

    return Scenario(
        name=f"reference_heterogeneous_iot_{profile_variant}",
        width_m=1000.0,
        height_m=1000.0,
        start=(50.0, 50.0),
        speed_mps=12.0,
        protocols=protocols,
        nodes=nodes,
        radio_obstacles=radio_obstacles,
        max_blackout_s=120.0,
        disconnect_gap_s=1.0,
    )


def build_random_scenario(
    seed: int,
    node_count: int = 14,
    width_m: float = 1000.0,
    height_m: float = 1000.0,
    profile_variant: str = "reference",
) -> Scenario:
    rng = random.Random(seed)
    protocols = _select_protocols(profile_variant)
    protocol_names = tuple(protocols)
    nodes = {}

    for index in range(1, node_count + 1):
        protocol = rng.choice(protocol_names)
        nodes[f"N{index:02d}"] = IoTNode(
            node_id=f"N{index:02d}",
            x_m=rng.uniform(90.0, width_m - 90.0),
            y_m=rng.uniform(90.0, height_m - 90.0),
            protocol=protocol,
            data_kb=_random_data_kb(rng, protocol),
            first_awake_s=rng.uniform(0.0, protocols[protocol].sleep_cycle_s * 0.75),
            priority=rng.uniform(0.8, 1.2),
        )

    radio_obstacles = (
        RadioObstacle(
            name="random 2.4GHz interference",
            x_m=rng.uniform(220.0, width_m - 220.0),
            y_m=rng.uniform(220.0, height_m - 220.0),
            radius_m=rng.uniform(120.0, 210.0),
            affected_protocols=("WiFi", "ZigBee", "BLE"),
            range_multiplier=rng.uniform(0.48, 0.70),
            data_rate_multiplier=rng.uniform(0.38, 0.68),
            loss_addition=rng.uniform(0.12, 0.28),
        ),
        RadioObstacle(
            name="random LPWAN shadow",
            x_m=rng.uniform(220.0, width_m - 220.0),
            y_m=rng.uniform(220.0, height_m - 220.0),
            radius_m=rng.uniform(110.0, 190.0),
            affected_protocols=("LoRa",),
            range_multiplier=rng.uniform(0.55, 0.78),
            data_rate_multiplier=rng.uniform(0.45, 0.75),
            loss_addition=rng.uniform(0.10, 0.24),
        ),
    )

    return Scenario(
        name=f"random_heterogeneous_iot_{profile_variant}_seed_{seed}",
        width_m=width_m,
        height_m=height_m,
        start=(50.0, 50.0),
        speed_mps=rng.uniform(10.0, 14.0),
        protocols=protocols,
        nodes=nodes,
        radio_obstacles=radio_obstacles,
        max_blackout_s=120.0,
        disconnect_gap_s=1.0,
    )


def _random_data_kb(rng: random.Random, protocol: str) -> float:
    if protocol == "WiFi":
        return rng.uniform(500.0, 1200.0)
    if protocol == "LoRa":
        return rng.uniform(140.0, 360.0)
    if protocol == "ZigBee":
        return rng.uniform(80.0, 220.0)
    return rng.uniform(50.0, 160.0)
