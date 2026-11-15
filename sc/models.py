from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Spot:
    spot_id: int
    name: str
    longitude: float
    latitude: float


@dataclass
class Edge:
    start: int
    end: int
    method: str
    distance: float
    time: float
    cost: float


@dataclass
class PathInfo:
    start: int
    end: int
    spots: list[int]
    edges: list[Edge]

    @property
    def distance(self) -> float:
        return sum(edge.distance for edge in self.edges)

    @property
    def time(self) -> float:
        return sum(edge.time for edge in self.edges)

    @property
    def cost(self) -> float:
        return sum(edge.cost for edge in self.edges)

    @property
    def stop_count(self) -> int:
        return max(0, len(self.spots) - 2)

    @property
    def path_length(self) -> int:
        return len(self.edges)


WeightFunction = Callable[[Edge], float]
