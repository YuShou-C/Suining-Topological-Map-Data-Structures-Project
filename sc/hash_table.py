from __future__ import annotations

from dataclasses import dataclass

from models import PathInfo


@dataclass
class HashNode:
    end_id: int
    path: PathInfo
    next: HashNode | None = None


class PathHashTable:
    """按终点编号散列、链地址法保存某个起点的路径集合。"""

    def __init__(self, size: int) -> None:
        self.size = max(1, size)
        self.buckets: list[HashNode | None] = [None] * self.size

    def _index(self, end_id: int) -> int:
        return end_id % self.size

    def clear(self) -> None:
        self.buckets = [None] * self.size

    def insert(self, path: PathInfo) -> None:
        index = self._index(path.end)
        node = HashNode(path.end, path)
        current = self.buckets[index]
        if current is None:
            self.buckets[index] = node
            return
        while current.next is not None:
            current = current.next
        current.next = node

    def search(self, end_id: int) -> list[PathInfo]:
        result: list[PathInfo] = []
        current = self.buckets[self._index(end_id)]
        while current is not None:
            if current.end_id == end_id:
                result.append(current.path)
            current = current.next
        return result

    def all_paths(self) -> list[PathInfo]:
        result: list[PathInfo] = []
        for bucket in self.buckets:
            current = bucket
            while current is not None:
                result.append(current.path)
                current = current.next
        return result
