from __future__ import annotations

import heapq
from collections import defaultdict

from hash_table import PathHashTable
from models import Edge, PathInfo, WeightFunction


class Graph:
    def __init__(self) -> None:
        self.adjacency: dict[int, list[Edge]] = defaultdict(list)

    def add_edge(self, edge: Edge, undirected: bool = True) -> None:
        self.adjacency[edge.start].append(edge)
        if undirected:
            self.adjacency[edge.end].append(
                Edge(edge.end, edge.start, edge.method, edge.distance, edge.time, edge.cost)
            )

    def edges(self) -> list[Edge]:
        return [edge for values in self.adjacency.values() for edge in values]

    def find_all_paths(
        self, start: int, end: int, include_transport_variants: bool = True
    ) -> list[PathInfo]:
        result: list[PathInfo] = []

        def dfs(current: int, visited: set[int], spots: list[int], edges: list[Edge]) -> None:
            if current == end:
                result.append(PathInfo(start, end, spots[:], edges[:]))
                return
            edges_to_visit = self.adjacency.get(current, [])
            if not include_transport_variants:
                best_edges: dict[int, Edge] = {}
                for edge in edges_to_visit:
                    old_edge = best_edges.get(edge.end)
                    if old_edge is None or (
                        edge.distance,
                        edge.time,
                        edge.cost,
                    ) < (old_edge.distance, old_edge.time, old_edge.cost):
                        best_edges[edge.end] = edge
                edges_to_visit = list(best_edges.values())
            for edge in edges_to_visit:
                if edge.end in visited:
                    continue
                visited.add(edge.end)
                spots.append(edge.end)
                edges.append(edge)
                dfs(edge.end, visited, spots, edges)
                edges.pop()
                spots.pop()
                visited.remove(edge.end)

        dfs(start, {start}, [start], [])
        return result

    def build_hash_table(self, spot_ids: list[int]) -> dict[int, PathHashTable]:
        tables = {spot_id: PathHashTable(len(spot_ids)) for spot_id in spot_ids}
        for start in spot_ids:
            for end in spot_ids:
                if start == end:
                    continue
                paths = self.find_all_paths(start, end)
                paths.sort(key=default_path_sort_key)
                for path in paths:
                    tables[start].insert(path)
        return tables

    def dijkstra(
        self, start: int, weight: WeightFunction
    ) -> tuple[dict[int, float], dict[int, tuple[int, Edge]]]:
        distances: dict[int, float] = {start: 0.0}
        previous: dict[int, tuple[int, Edge]] = {}
        queue: list[tuple[float, int]] = [(0.0, start)]
        while queue:
            current_distance, current = heapq.heappop(queue)
            if current_distance != distances[current]:
                continue
            for edge in self.adjacency.get(current, []):
                candidate = current_distance + weight(edge)
                if candidate < distances.get(edge.end, float("inf")):
                    distances[edge.end] = candidate
                    previous[edge.end] = (current, edge)
                    heapq.heappush(queue, (candidate, edge.end))
        return distances, previous


def default_path_sort_key(path: PathInfo) -> tuple[float, ...]:
    return (path.end, path.stop_count, path.time, path.cost, path.path_length)


def sort_paths(paths: list[PathInfo], criterion: str) -> list[PathInfo]:
    key_map = {
        "路径长度": lambda path: (path.distance, path.time, path.cost, path.stop_count),
        "花费时间": lambda path: (path.time, path.distance, path.cost, path.stop_count),
        "费用": lambda path: (path.cost, path.time, path.distance, path.stop_count),
        "途经景点数": lambda path: (path.stop_count, path.distance, path.time, path.cost),
    }
    return sorted(paths, key=key_map[criterion])


def rebuild_path(
    previous: dict[int, tuple[int, Edge]], start: int, target: int
) -> PathInfo | None:
    if target != start and target not in previous:
        return None
    edges: list[Edge] = []
    spots = [target]
    current = target
    while current != start:
        previous_spot, edge = previous[current]
        edges.append(edge)
        spots.append(previous_spot)
        current = previous_spot
    edges.reverse()
    spots.reverse()
    return PathInfo(start, target, spots, edges)
