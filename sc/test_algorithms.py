import unittest

from algorithms import Graph, rebuild_path, sort_paths
from hash_table import PathHashTable
from models import Edge
from sample_data import EDGES, SPOTS


class AlgorithmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = Graph()
        self.graph.add_edge(Edge(1, 2, "步行", 1, 10, 0))
        self.graph.add_edge(Edge(2, 3, "公交车", 2, 5, 2))
        self.graph.add_edge(Edge(1, 3, "自驾", 5, 3, 5))

    def test_all_simple_paths_and_hash_search(self) -> None:
        paths = self.graph.find_all_paths(1, 3)
        self.assertEqual(len(paths), 2)
        table = PathHashTable(3)
        for path in paths:
            table.insert(path)
        self.assertEqual(len(table.search(3)), 2)

    def test_sorting(self) -> None:
        paths = self.graph.find_all_paths(1, 3)
        ordered = sort_paths(paths, "路径长度")
        self.assertEqual(ordered[0].distance, 3)

    def test_dijkstra(self) -> None:
        distances, previous = self.graph.dijkstra(1, lambda edge: edge.time)
        self.assertEqual(distances[3], 3)
        path = rebuild_path(previous, 1, 3)
        self.assertIsNotNone(path)
        self.assertEqual(path.edges[0].method, "自驾")

    def test_sample_data_has_ten_connected_spots(self) -> None:
        graph = Graph()
        for edge in EDGES:
            graph.add_edge(edge)
        self.assertEqual(len(SPOTS), 10)
        self.assertEqual(set(graph.adjacency), set(range(1, 11)))
        self.assertTrue(graph.find_all_paths(1, 10))
        self.assertEqual({edge.method for edge in EDGES}, {"步行", "公交车", "自驾"})


if __name__ == "__main__":
    unittest.main()
