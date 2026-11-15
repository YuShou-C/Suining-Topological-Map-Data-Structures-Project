from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from algorithms import Graph, default_path_sort_key, rebuild_path
from models import PathInfo, Spot
from sample_data import EDGES, SPOTS


METHOD_COLORS = {
    "步行": "#4c9f70",
    "公交车": "#3d78b5",
    "自驾": "#d28a35",
}


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
        ttk.Label(shortest, text="距离、时间、费用分别计算到每个可达景点").pack(anchor="w", pady=(6, 0))

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
        self.path_tables = self.graph.build_hash_table(list(self.spots))

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
        drawn: set[tuple[int, int, str]] = set()
        for edge in self.graph.edges():
            reverse_key = (edge.end, edge.start, edge.method)
            key = (edge.start, edge.end, edge.method)
            if reverse_key in drawn:
                continue
            start, end = self.spots.get(edge.start), self.spots.get(edge.end)
            if not start or not end:
                continue
            x1, y1 = point(start)
            x2, y2 = point(end)
            selected = key in highlight_edges or reverse_key in highlight_edges
            self.canvas.create_line(x1, y1, x2, y2,
                                    fill="#d94b4b" if selected else METHOD_COLORS.get(edge.method, "#a7b5c5"),
                                    width=4 if selected else 1, dash=() if selected else (4, 3))
            drawn.add(key)
        for spot in self.spots.values():
            x, y = point(spot)
            fill = "#f39c12" if highlight and spot.spot_id in highlight.spots else "#2878b5"
            self.canvas.create_oval(x - 9, y - 9, x + 9, y + 9, fill=fill, outline="white", width=2)
            self.canvas.create_text(x, y - 20, text=f"{spot.spot_id}. {spot.name}", fill="#1f2d3d")
        self.canvas.create_text(15, 15, anchor="nw", text="遂宁市景点简易拓扑地图", fill="#315a7d", font=("微软雅黑", 13, "bold"))
        legend_x, legend_y = 15, 42
        self.canvas.create_text(legend_x, legend_y, anchor="nw", text="出行方式：", fill="#1f2d3d")
        for index, method in enumerate(("步行", "公交车", "自驾")):
            x = legend_x + 72 + index * 75
            self.canvas.create_line(x, legend_y + 7, x + 20, legend_y + 7,
                                    fill=METHOD_COLORS[method], width=3)
            self.canvas.create_text(x + 25, legend_y + 7, anchor="w", text=method, fill="#1f2d3d")

    def _query_paths(self) -> None:
        try:
            start, end = self.name_to_id[self.query_start.get()], self.name_to_id[self.query_end.get()]
            if start == end:
                raise ValueError("起点和终点不能相同")
            self.current_paths = self.path_tables[start].search(end)
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
        if self.result_mode != "paths":
            return
        selection = self.result.curselection()
        if selection and selection[0] < len(self.current_paths):
            self._draw_map(self.current_paths[selection[0]])

    def _shortest_paths(self) -> None:
        if self.query_start.get() not in self.name_to_id:
            messagebox.showerror("查询错误", "请选择起点")
            return
        start = self.name_to_id[self.query_start.get()]
        self.result.delete(0, tk.END)
        self.result.selection_clear(0, tk.END)
        self.current_paths = []
        self.result_mode = "shortest"
        for title, weight in (("距离最短", lambda edge: edge.distance), ("时间最短", lambda edge: edge.time), ("费用最少", lambda edge: edge.cost)):
            _, previous = self.graph.dijkstra(start, weight)
            self.result.insert(tk.END, f"【{title}】")
            for target in self.spots:
                if target == start:
                    continue
                path = rebuild_path(previous, start, target)
                if path is None:
                    self.result.insert(tk.END, f"  -> {self.spots[target].name}：不可达")
                else:
                    self.result.insert(tk.END, f"  -> {self.spots[target].name}：{path.distance:.1f}km/{path.time:.0f}min/{path.cost:.1f}元")
        self.result.yview_moveto(0)
        self.status.configure(text="三类最优路径计算完成")


def main() -> None:
    root = tk.Tk()
    ScenicMapApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
