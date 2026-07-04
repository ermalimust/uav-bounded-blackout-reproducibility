from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from .geometry import distance_m, inside_obstacle
from .models import IoTNode, Scenario, SimulationResult, SimulationState, VisitEstimate


def wait_until_awake(arrival_time_s: float, node: IoTNode, scenario: Scenario) -> float:
    protocol = scenario.protocols[node.protocol]
    if protocol.sleep_cycle_s <= 0 or protocol.awake_window_s >= protocol.sleep_cycle_s:
        return 0.0

    phase = (arrival_time_s - node.first_awake_s) % protocol.sleep_cycle_s
    if phase <= protocol.awake_window_s:
        return 0.0
    return protocol.sleep_cycle_s - phase


def active_radio_obstacles(node: IoTNode, scenario: Scenario) -> Tuple[str, ...]:
    hits: List[str] = []
    for obstacle in scenario.radio_obstacles:
        if node.protocol in obstacle.affected_protocols and inside_obstacle(node.point, obstacle):
            hits.append(obstacle.name)
    return tuple(hits)


def _radio_modifiers(node: IoTNode, scenario: Scenario) -> Tuple[float, float, float, int]:
    range_factor = 1.0
    rate_factor = 1.0
    loss_addition = 0.0
    hit_count = 0

    for obstacle in scenario.radio_obstacles:
        if node.protocol not in obstacle.affected_protocols:
            continue
        if not inside_obstacle(node.point, obstacle):
            continue
        range_factor *= obstacle.range_multiplier
        rate_factor *= obstacle.data_rate_multiplier
        loss_addition += obstacle.loss_addition
        hit_count += 1

    return range_factor, rate_factor, loss_addition, hit_count


def initial_state(scenario: Scenario) -> SimulationState:
    return SimulationState(
        current_point=scenario.start,
        current_time_s=0.0,
        last_comm_time_s=0.0,
        last_protocol=None,
    )


def estimate_visit(scenario: Scenario, state: SimulationState, node: IoTNode) -> VisitEstimate:
    protocol = scenario.protocols[node.protocol]
    travel_s = distance_m(state.current_point, node.point) / scenario.speed_mps
    arrival_s = state.current_time_s + travel_s
    wait_s = wait_until_awake(arrival_s, node, scenario)

    _, rate_factor, loss_addition, hit_count = _radio_modifiers(node, scenario)
    packet_loss = min(0.92, max(0.0, protocol.packet_loss_at_edge * 0.35 + loss_addition))
    effective_rate_kb_s = max(0.01, (protocol.data_rate_kbps / 8.0) * rate_factor * (1.0 - packet_loss))

    switch_s = 0.0
    if state.last_protocol is not None and state.last_protocol != protocol.name:
        switch_s = protocol.switch_penalty_s

    gap_before_setup_s = arrival_s + wait_s - state.last_comm_time_s
    setup_s = protocol.connection_setup_s
    reconnected = gap_before_setup_s > protocol.disconnect_threshold_s
    if reconnected:
        setup_s += protocol.reconnect_penalty_s

    communication_gap_s = gap_before_setup_s + setup_s + switch_s
    transfer_s = node.data_kb / effective_rate_kb_s

    return VisitEstimate(
        travel_s=travel_s,
        wait_s=wait_s,
        setup_s=setup_s,
        switch_s=switch_s,
        transfer_s=transfer_s,
        communication_gap_s=communication_gap_s,
        radio_obstacle_hits=hit_count,
        reconnected=reconnected,
    )


def advance_state(
    scenario: Scenario, state: SimulationState, node: IoTNode
) -> Tuple[SimulationState, VisitEstimate]:
    estimate = estimate_visit(scenario, state, node)
    next_time_s = state.current_time_s + estimate.total_s
    next_state = SimulationState(
        current_point=node.point,
        current_time_s=next_time_s,
        last_comm_time_s=next_time_s,
        last_protocol=scenario.protocols[node.protocol].name,
    )
    return next_state, estimate


def simulate_route(scenario: Scenario, route: Iterable[str]) -> SimulationResult:
    state = initial_state(scenario)
    route_tuple = tuple(route)
    collected: List[str] = []
    failed: List[str] = []
    events: List[Dict[str, object]] = []

    flight_distance_m = 0.0
    service_time_s = 0.0
    wait_time_s = 0.0
    max_blackout_s = 0.0
    reconnect_count = 0
    protocol_switches = 0
    radio_obstacle_hits = 0

    for node_id in route_tuple:
        node = scenario.nodes[node_id]
        previous_state = state
        state, estimate = advance_state(scenario, state, node)

        flight_distance_m += estimate.travel_s * scenario.speed_mps
        service_time_s += estimate.setup_s + estimate.switch_s + estimate.transfer_s
        wait_time_s += estimate.wait_s
        max_blackout_s = max(max_blackout_s, estimate.communication_gap_s)
        radio_obstacle_hits += estimate.radio_obstacle_hits

        if estimate.reconnected:
            reconnect_count += 1
        if estimate.switch_s > 0:
            protocol_switches += 1

        collected.append(node_id)
        events.append(
            {
                "node": node_id,
                "protocol": node.protocol,
                "arrival_s": round(previous_state.current_time_s + estimate.travel_s, 3),
                "wait_s": round(estimate.wait_s, 3),
                "setup_s": round(estimate.setup_s, 3),
                "switch_s": round(estimate.switch_s, 3),
                "transfer_s": round(estimate.transfer_s, 3),
                "completion_s": round(state.current_time_s, 3),
                "communication_gap_s": round(estimate.communication_gap_s, 3),
                "disconnect_threshold_s": round(
                    scenario.protocols[node.protocol].disconnect_threshold_s, 3
                ),
                "reconnected": estimate.reconnected,
                "radio_obstacles": active_radio_obstacles(node, scenario),
            }
        )

    return_home_s = distance_m(state.current_point, scenario.start) / scenario.speed_mps
    flight_distance_m += return_home_s * scenario.speed_mps
    total_time_s = state.current_time_s + return_home_s
    max_blackout_s = max(max_blackout_s, total_time_s - state.last_comm_time_s)

    node_count = len(scenario.nodes)
    data_success_rate = len(collected) / node_count if node_count else 1.0

    return SimulationResult(
        route=route_tuple,
        total_time_s=total_time_s,
        flight_distance_m=flight_distance_m,
        service_time_s=service_time_s,
        wait_time_s=wait_time_s,
        data_success_rate=data_success_rate,
        max_blackout_s=max_blackout_s,
        reconnect_count=reconnect_count,
        protocol_switches=protocol_switches,
        radio_obstacle_hits=radio_obstacle_hits,
        collected_nodes=tuple(collected),
        failed_nodes=tuple(failed),
        event_log=tuple(events),
    )
