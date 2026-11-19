from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from algorithms import Graph, default_path_sort_key, rebuild_path
from hash_table import PathHashTable
from models import PathInfo, Spot
from sample_data import EDGES, SPOTS


class ScenicMapApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("遂宁市景点地图服务系统")
        self.root.geometry("1260x760")
        self.spots: dict[int, Spot] = {spot.spot_id: spot for spot in SPOTS}
        self.graph = Graph()
        for edge in EDGES:
            self.graph.add_edge(edge)
        self.path_tables = {}
        self.current_paths: list[PathInfo] = []
        self.result_mode = "paths"
        self.name_to_id: dict[str, int] = {}
        self._build_ui()
        self._refresh_spots()
        self._rebuild_paths()
        self._draw_map()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        center = ttk.Frame(self.root, padding=10)
        center.grid(row=0, column=0, sticky="nsew")
        center.rowconfigure(0, weight=1)
        center.columnconfigure(0, weight=1)
        right = ttk.Frame(self.root, padding=(0, 10, 10, 0))
        right.grid(row=0, column=1, sticky="ns")

        self.canvas = tk.Canvas(center, bg="#f4f7fb", highlightthickness=1, highlightbackground="#b7c5d6")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _: self._draw_map())

        self._build_query_panel(right)

    def _build_query_panel(self, parent: ttk.Frame) -> None:
        query = ttk.LabelFrame(parent, text="路径查询", padding=8)
        query.pack(fill="x", pady=(0, 10))
        self.query_start = tk.StringVar()
        self.query_end = tk.StringVar()
        ttk.Label(query, text="起点名称").pack(anchor="w")
        self.start_combo = ttk.Combobox(query, textvariable=self.query_start, state="readonly", width=28)
        self.start_combo.pack(fill="x", pady=(0, 4))
        ttk.Label(query, text="终点名称").pack(anchor="w")
        self.end_combo = ttk.Combobox(query, textvariable=self.query_end, state="readonly", width=28)
        self.end_combo.pack(fill="x", pady=(0, 4))
        ttk.Button(query, text="查询所有路径", command=self._query_paths).pack(fill="x", pady=(4, 0))

        shortest = ttk.LabelFrame(parent, text="从起点出发的最优路径", padding=8)
        shortest.pack(fill="x", pady=(0, 10))
        ttk.Button(shortest, text="计算三类最优路径", command=self._shortest_paths).pack(fill="x")
        ttk.Label(shortest, text="先找距离最短路线，再分别展示自驾和步行方案").pack(anchor="w", pady=(6, 0))

        result_frame = ttk.Frame(parent)
        result_frame.pack(fill="both", expand=True)
        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)
        self.result = tk.Listbox(result_frame, width=48, height=20)
        self.result.grid(row=0, column=0, sticky="nsew")
        result_scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result.yview)
        result_scrollbar.grid(row=0, column=1, sticky="ns")
        self.result.configure(yscrollcommand=result_scrollbar.set)
        self.result.bind("<<ListboxSelect>>", self._select_result)
        self.status = ttk.Label(parent, text="就绪", foreground="#315a7d")
        self.status.pack(anchor="w", pady=(6, 0))

    def _refresh_spots(self) -> None:
        self.name_to_id = {spot.name: spot.spot_id for spot in self.spots.values()}
        names = list(self.name_to_id)
        self.start_combo["values"] = names
        self.end_combo["values"] = names

    def _rebuild_paths(self) -> None:
        self.path_tables = {}

    def _draw_map(self, highlight: PathInfo | None = None) -> None:
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("all")
        if not self.spots:
            return
        width = max(self.canvas.winfo_width(), 600)
        height = max(self.canvas.winfo_height(), 500)
        longitudes = [spot.longitude for spot in self.spots.values()]
        latitudes = [spot.latitude for spot in self.spots.values()]
        min_lon, max_lon = min(longitudes), max(longitudes)
        min_lat, max_lat = min(latitudes), max(latitudes)

        def point(spot: Spot) -> tuple[float, float]:
            x = 50 + (spot.longitude - min_lon) / max(max_lon - min_lon, 0.001) * (width - 100)
            y = height - 50 - (spot.latitude - min_lat) / max(max_lat - min_lat, 0.001) * (height - 100)
            return x, y

        highlight_edges = {(edge.start, edge.end, edge.method) for edge in (highlight.edges if highlight else [])}
        drawn: set[tuple[int, int]] = set()
        for edge in self.graph.edges():
            pair = tuple(sorted((edge.start, edge.end)))
            if pair in drawn:
                continue
            start, end = self.spots.get(edge.start), self.spots.get(edge.end)
            if not start or not end:
                continue
            x1, y1 = point(start)
            x2, y2 = point(end)
            selected = any(
                (candidate.start, candidate.end, candidate.method) in highlight_edges
                or (candidate.end, candidate.start, candidate.method) in highlight_edges
                for candidate in self.graph.adjacency.get(edge.start, [])
                if candidate.end == edge.end
            )
            self.canvas.create_line(x1, y1, x2, y2, fill="black", width=4 if selected else 1)
            drawn.add(pair)
        for spot in self.spots.values():
            x, y = point(spot)
            fill = "#f39c12" if highlight and spot.spot_id in highlight.spots else "#2878b5"
            self.canvas.create_oval(x - 9, y - 9, x + 9, y + 9, fill=fill, outline="white", width=2)
            self.canvas.create_text(x, y - 20, text=f"{spot.spot_id}. {spot.name}", fill="#1f2d3d")
        self.canvas.create_text(15, 15, anchor="nw", text="遂宁市景点简易拓扑地图", fill="#315a7d", font=("微软雅黑", 13, "bold"))

    def _query_paths(self) -> None:
        try:
            start, end = self.name_to_id[self.query_start.get()], self.name_to_id[self.query_end.get()]
            if start == end:
                raise ValueError("起点和终点不能相同")
            table = PathHashTable(len(self.spots))
            paths = self.graph.find_all_paths(start, end, include_transport_variants=False)
            paths.sort(key=default_path_sort_key)
            for path in paths:
                table.insert(path)
            self.path_tables[start] = table
            self.current_paths = table.search(end)
            self.result_mode = "paths"
            self._show_paths()
            self.status.configure(text=f"共找到 {len(self.current_paths)} 条路径")
        except KeyError:
            messagebox.showerror("查询错误", "请选择起点和终点")
        except ValueError as exc:
            messagebox.showerror("查询错误", str(exc))

    def _show_paths(self) -> None:
        if self.result_mode != "paths":
            return
        self.current_paths.sort(key=default_path_sort_key)
        self.result.delete(0, tk.END)
        self.result.selection_clear(0, tk.END)
        for index, path in enumerate(self.current_paths, 1):
            names = " -> ".join(self.spots[spot_id].name for spot_id in path.spots)
            methods = "、".join(edge.method for edge in path.edges)
            self.result.insert(tk.END, f"{index}. {names} | {methods} | {path.distance:.1f}km | {path.time:.0f}min | {path.cost:.1f}元 | {path.stop_count}个途经点")
        self.result.yview_moveto(0)

    def _select_result(self, _: object = None) -> None:
        if self.result_mode not in ("paths", "shortest"):
            return
        selection = self.result.curselection()
        if selection and selection[0] < len(self.current_paths):
            self._draw_map(self.current_paths[selection[0]])

    def _path_with_method(self, path: PathInfo, method: str) -> PathInfo:
        edges = []
        for route_edge in path.edges:
            matching_edges = [
                edge
                for edge in self.graph.adjacency.get(route_edge.start, [])
                if edge.end == route_edge.end and edge.method == method
            ]
            if not matching_edges:
                raise ValueError(f"缺少{method}路径：{route_edge.start} -> {route_edge.end}")
            edges.append(matching_edges[0])
        return PathInfo(path.start, path.end, path.spots[:], edges)

    def _shortest_paths(self) -> None:
        if self.query_start.get() not in self.name_to_id or self.query_end.get() not in self.name_to_id:
            messagebox.showerror("查询错误", "请选择起点和终点")
            return
        start = self.name_to_id[self.query_start.get()]
        end = self.name_to_id[self.query_end.get()]
        if start == end:
            messagebox.showerror("查询错误", "起点和终点不能相同")
            return
        self.result.delete(0, tk.END)
        self.result.selection_clear(0, tk.END)
        self.current_paths = []
        self.result_mode = "shortest"
        _, previous = self.graph.dijkstra(start, lambda edge: edge.distance)
        distance_path = rebuild_path(previous, start, end)
        if distance_path is None:
            self.result.insert(tk.END, "三个方案均不可达")
            self.result.yview_moveto(0)
            self.status.configure(text=f"{self.spots[start].name} 到 {self.spots[end].name} 不可达")
            return

        driving_path = self._path_with_method(distance_path, "自驾")
        walking_path = self._path_with_method(distance_path, "步行")
        self.current_paths = [distance_path, driving_path, walking_path]
        names = " -> ".join(self.spots[spot_id].name for spot_id in distance_path.spots)
        self.result.insert(
            tk.END,
            f"【距离最短】{names} | 距离：{distance_path.distance:.1f}km",
        )
        for title, path in (("时间最短（自驾）", driving_path), ("费用最少（步行）", walking_path)):
            methods = "、".join(edge.method for edge in path.edges)
            self.result.insert(
                tk.END,
                f"【{title}】{names} | {methods} | "
                f"距离：{path.distance:.1f}km | 时间：{path.time:.0f}min | 费用：{path.cost:.1f}元",
            )
        self.result.yview_moveto(0)
        self.status.configure(text=f"{self.spots[start].name} 到 {self.spots[end].name} 的三类最优路径计算完成")


def main() -> None:
    root = tk.Tk()
    ScenicMapApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
