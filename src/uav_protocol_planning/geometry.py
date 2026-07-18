from __future__ import annotations

import math

from .models import Point, RadioObstacle


def distance_m(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def inside_obstacle(point: Point, obstacle: RadioObstacle) -> bool:
    return distance_m(point, obstacle.point) <= obstacle.radius_m


def contact_point_on_segment(start: Point, target: Point, contact_range_m: float) -> Point:
    """Return the first point on start->target within ``contact_range_m`` of target."""
    direct_distance_m = distance_m(start, target)
    if direct_distance_m <= contact_range_m or direct_distance_m == 0.0:
        return start

    travel_fraction = (direct_distance_m - contact_range_m) / direct_distance_m
    return (
        start[0] + travel_fraction * (target[0] - start[0]),
        start[1] + travel_fraction * (target[1] - start[1]),
    )
