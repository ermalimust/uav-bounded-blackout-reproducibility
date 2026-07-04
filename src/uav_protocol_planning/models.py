from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Sequence, Tuple

Point = Tuple[float, float]


@dataclass(frozen=True)
class ProtocolProfile:
    name: str
    nominal_range_m: float
    data_rate_kbps: float
    connection_setup_s: float
    reconnect_penalty_s: float
    sleep_cycle_s: float
    awake_window_s: float
    packet_loss_at_edge: float
    switch_penalty_s: float
    disconnect_threshold_s: float = 1.0


@dataclass(frozen=True)
class IoTNode:
    node_id: str
    x_m: float
    y_m: float
    protocol: str
    data_kb: float
    first_awake_s: float = 0.0
    priority: float = 1.0

    @property
    def point(self) -> Point:
        return (self.x_m, self.y_m)


@dataclass(frozen=True)
class RadioObstacle:
    name: str
    x_m: float
    y_m: float
    radius_m: float
    affected_protocols: Tuple[str, ...]
    range_multiplier: float
    data_rate_multiplier: float
    loss_addition: float

    @property
    def point(self) -> Point:
        return (self.x_m, self.y_m)


@dataclass(frozen=True)
class Scenario:
    name: str
    width_m: float
    height_m: float
    start: Point
    speed_mps: float
    protocols: Mapping[str, ProtocolProfile]
    nodes: Mapping[str, IoTNode]
    radio_obstacles: Sequence[RadioObstacle]
    max_blackout_s: float = 120.0
    disconnect_gap_s: float = 1.0


@dataclass(frozen=True)
class VisitEstimate:
    travel_s: float
    wait_s: float
    setup_s: float
    switch_s: float
    transfer_s: float
    communication_gap_s: float
    radio_obstacle_hits: int
    reconnected: bool

    @property
    def total_s(self) -> float:
        return self.travel_s + self.wait_s + self.setup_s + self.switch_s + self.transfer_s


@dataclass(frozen=True)
class SimulationState:
    current_point: Point
    current_time_s: float
    last_comm_time_s: float
    last_protocol: str | None


@dataclass(frozen=True)
class SimulationResult:
    route: Tuple[str, ...]
    total_time_s: float
    flight_distance_m: float
    service_time_s: float
    wait_time_s: float
    data_success_rate: float
    max_blackout_s: float
    reconnect_count: int
    protocol_switches: int
    radio_obstacle_hits: int
    collected_nodes: Tuple[str, ...]
    failed_nodes: Tuple[str, ...]
    event_log: Tuple[Dict[str, object], ...]
