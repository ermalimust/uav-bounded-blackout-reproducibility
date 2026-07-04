"""Protocol-aware UAV path planning research prototype."""

from .models import IoTNode, ProtocolProfile, RadioObstacle, Scenario
from .planners import (
    distance_only_route,
    genetic_algorithm_route,
    ordinary_data_collection_route,
    particle_swarm_route,
    protocol_aware_route,
)
from .scenarios import build_reference_scenario
from .simulation import simulate_route

__all__ = [
    "IoTNode",
    "ProtocolProfile",
    "RadioObstacle",
    "Scenario",
    "build_reference_scenario",
    "distance_only_route",
    "genetic_algorithm_route",
    "ordinary_data_collection_route",
    "particle_swarm_route",
    "protocol_aware_route",
    "simulate_route",
]
