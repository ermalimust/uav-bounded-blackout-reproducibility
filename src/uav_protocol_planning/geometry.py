from __future__ import annotations

import math

from .models import Point, RadioObstacle


def distance_m(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def inside_obstacle(point: Point, obstacle: RadioObstacle) -> bool:
    return distance_m(point, obstacle.point) <= obstacle.radius_m
