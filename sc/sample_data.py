from models import Edge, Spot


SPOTS = [
    Spot(1, "观音湖湿地公园", 105.592, 30.508),
    Spot(2, "广德寺", 105.548, 30.525),
    Spot(3, "灵泉寺", 105.625, 30.500),
    Spot(4, "遂宁市人民公园", 105.568, 30.526),
    Spot(5, "遂宁市博物馆", 105.579, 30.507),
    Spot(6, "圣莲岛", 105.602, 30.493),
    Spot(7, "涪江文化长廊", 105.575, 30.515),
    Spot(8, "西山森林公园", 105.555, 30.535),
    Spot(9, "遂宁市体育中心", 105.566, 30.491),
    Spot(10, "遂宁火车站", 105.564, 30.551),
]


CONNECTIONS = [
    (1, 5, 2.4),
    (1, 6, 1.8),
    (1, 7, 2.0),
    (2, 5, 3.1),
    (2, 7, 2.8),
    (2, 4, 3.8),
    (3, 1, 5.2),
    (3, 6, 4.0),
    (4, 8, 2.0),
    (5, 7, 1.2),
    (5, 6, 2.6),
    (6, 7, 1.6),
    (2, 8, 1.7),
    (7, 8, 2.1),
    (7, 9, 3.0),
    (6, 9, 2.7),
    (8, 10, 2.4),
    (9, 10, 4.1),
]


def _three_mode_edges(start: int, end: int, distance: float) -> list[Edge]:
    return [
        Edge(start, end, "步行", distance, round(distance * 15), 0),
        Edge(start, end, "公交车", round(distance * 1.08, 1), round(distance * 5 + 5), 2),
        Edge(start, end, "自驾", round(distance * 1.03, 1), max(3, round(distance * 2.5)), max(3, round(distance * 1.5))),
    ]


EDGES = [
    edge
    for start, end, distance in CONNECTIONS
    for edge in _three_mode_edges(start, end, distance)
]
