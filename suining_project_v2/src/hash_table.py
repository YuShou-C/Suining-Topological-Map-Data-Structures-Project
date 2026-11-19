from __future__ import annotations

from dataclasses import dataclass

from models import PathInfo, path_order_key


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
        """按 path_order_key 升序插入，保证桶内链表始终有序。"""
        index = self._index(path.end)
        node = HashNode(path.end, path)
        key = path_order_key(path)
        head = self.buckets[index]
        # 空桶，或比头结点更小：插到最前面
        if head is None or key < path_order_key(head.path):
            node.next = head
            self.buckets[index] = node
            return
        # 找到第一个键值大于 node 的前驱，插在其后
        current = head
        while current.next is not None and path_order_key(current.next.path) <= key:
            current = current.next
        node.next = current.next
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
