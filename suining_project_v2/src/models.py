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


def path_order_key(path: PathInfo) -> tuple[float, ...]:
    """路径排序键：终点编号 → 途经景点数 → 花费时间 → 费用 → 路径长度（升序）。"""
    return (path.end, path.stop_count, path.time, path.cost, path.path_length)


WeightFunction = Callable[[Edge], float]
