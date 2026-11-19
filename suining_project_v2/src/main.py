from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from algorithms import Graph, default_path_sort_key, rebuild_path, sort_paths
from models import PathInfo, Spot
from sample_data import EDGES, SPOTS


# 统一配色：主色 / 背景 / 卡片 / 画布 / 正文 / 次文
COLORS = {
    "primary": "#2c7be5",
    "primary_dark": "#1e64c4",
    "bg": "#eef2f7",
    "card": "#ffffff",
    "canvas": "#f7fafc",
    "text": "#1a202c",
    "muted": "#4a5568",
    "border": "#cbd5e0",
    "highlight_edge": "#e53e3e",
    "highlight_spot": "#ed8936",
    "highlight_spot_outline": "#c05621",
    "spot": "#2c7be5",
}

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

    # ---------- 样式 ----------
    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", font=("微软雅黑", 10))
        style.configure("TLabel", background=COLORS["card"], foreground=COLORS["text"])
        style.configure("TLabelframe", background=COLORS["card"], bordercolor=COLORS["border"])
        style.configure("TLabelframe.Label", background=COLORS["card"],
                        foreground=COLORS["primary"], font=("微软雅黑", 10, "bold"))
        style.configure("TButton", background=COLORS["primary"], foreground="#ffffff",
                        borderwidth=0, focusthickness=0, padding=(10, 6),
                        font=("微软雅黑", 10))
        style.map("TButton",
                  background=[("active", COLORS["primary_dark"]),
                              ("pressed", "#1a56a8")],
                  foreground=[("disabled", "#a0aec0")])
        style.configure("TCombobox", fieldbackground=COLORS["card"],
                        background=COLORS["card"], foreground=COLORS["text"],
                        arrowcolor=COLORS["primary"])
        style.configure("Vertical.TScrollbar", background="#e2e8f0",
                        troughcolor=COLORS["canvas"], bordercolor="#e2e8f0")

    # ---------- 布局 ----------
    def _build_ui(self) -> None:
        self._configure_styles()
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(1024, 640)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(1, weight=1)

        # 顶部标题栏
        header = tk.Frame(self.root, bg=COLORS["primary"], height=52)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.pack_propagate(False)
        tk.Label(header, text="遂宁市景点地图服务系统", bg=COLORS["primary"],
                 fg="#ffffff", font=("微软雅黑", 15, "bold")).pack(side="left", padx=18)
        tk.Label(header, text="数据结构课程设计 · 路径查询与最优路径分析",
                 bg=COLORS["primary"], fg="#dbeafe",
                 font=("微软雅黑", 9)).pack(side="right", padx=18)

        # 左侧：地图卡片
        left = tk.Frame(self.root, bg=COLORS["card"],
                        highlightbackground=COLORS["border"], highlightthickness=1)
        left.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=12)
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(left, bg=COLORS["canvas"], highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.canvas.bind("<Configure>", lambda _: self._draw_map())

        # 右侧：查询卡片
        right = tk.Frame(self.root, bg=COLORS["card"], width=400,
                         highlightbackground=COLORS["border"], highlightthickness=1)
        right.grid(row=1, column=1, sticky="ns", padx=(6, 12), pady=12)
        right.pack_propagate(False)
        self._build_query_panel(right)

    def _build_query_panel(self, parent: tk.Frame) -> None:
        inner = tk.Frame(parent, bg=COLORS["card"])
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        query = ttk.LabelFrame(inner, text="路径查询", padding=8)
        query.pack(fill="x", pady=(0, 10))
        self.query_start = tk.StringVar()
        self.query_end = tk.StringVar()
        ttk.Label(query, text="起点名称").pack(anchor="w")
        self.start_combo = ttk.Combobox(query, textvariable=self.query_start,
                                        state="readonly", width=28)
        self.start_combo.pack(fill="x", pady=(0, 6))
        ttk.Label(query, text="终点名称").pack(anchor="w")
        self.end_combo = ttk.Combobox(query, textvariable=self.query_end,
                                      state="readonly", width=28)
        self.end_combo.pack(fill="x", pady=(0, 6))
        ttk.Label(query, text="排序方式").pack(anchor="w")
        self.sort_criterion = tk.StringVar(value="默认顺序")
        self.sort_combo = ttk.Combobox(query, textvariable=self.sort_criterion,
                                       state="readonly", width=28)
        self.sort_combo["values"] = ["默认顺序", "路径长度", "花费时间", "费用", "途经景点数"]
        self.sort_combo.pack(fill="x", pady=(0, 6))
        self.sort_combo.bind("<<ComboboxSelected>>", lambda _: self._resort_current())
        ttk.Button(query, text="查询所有路径", command=self._query_paths).pack(fill="x", pady=(4, 0))

        shortest = ttk.LabelFrame(inner, text="从起点出发的最优路径", padding=8)
        shortest.pack(fill="x", pady=(0, 10))
        ttk.Button(shortest, text="计算三类最优路径",
                   command=self._shortest_paths).pack(fill="x")
        ttk.Label(shortest, text="距离 / 时间 / 费用分别计算到每个可达景点",
                  foreground=COLORS["muted"]).pack(anchor="w", pady=(6, 0))

        result_frame = tk.Frame(inner, bg=COLORS["card"])
        result_frame.pack(fill="both", expand=True)
        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)
        self.result = tk.Listbox(result_frame, width=32, height=18,
                                 font=("微软雅黑", 10), bg=COLORS["card"],
                                 fg=COLORS["text"], selectbackground=COLORS["primary"],
                                 selectforeground="#ffffff", activestyle="none",
                                 highlightthickness=1, highlightbackground=COLORS["border"],
                                 borderwidth=0, relief="flat")
        self.result.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(result_frame, orient="vertical", command=self.result.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(result_frame, orient="horizontal", command=self.result.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self.result.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.result.bind("<<ListboxSelect>>", self._select_result)

        self.status = tk.Label(inner, text="就绪", bg="#f1f5f9", fg=COLORS["primary"],
                               font=("微软雅黑", 9), anchor="w", padx=8, pady=5)
        self.status.pack(fill="x", pady=(10, 0))

    # ---------- 数据 ----------
    def _refresh_spots(self) -> None:
        self.name_to_id = {spot.name: spot.spot_id for spot in self.spots.values()}
        names = list(self.name_to_id)
        self.start_combo["values"] = names
        self.end_combo["values"] = names

    def _rebuild_paths(self) -> None:
        self.path_tables = self.graph.build_hash_table(list(self.spots))

    # ---------- 地图绘制 ----------
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

        highlight_edges = {(edge.start, edge.end, edge.method)
                           for edge in (highlight.edges if highlight else [])}
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
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=COLORS["highlight_edge"] if selected else METHOD_COLORS.get(edge.method, "#a7b5c5"),
                width=5 if selected else 2)
            drawn.add(key)

        for spot in self.spots.values():
            x, y = point(spot)
            highlighted = bool(highlight and spot.spot_id in highlight.spots)
            fill = COLORS["highlight_spot"] if highlighted else COLORS["spot"]
            outline = COLORS["highlight_spot_outline"] if highlighted else "#ffffff"
            ow = 3 if highlighted else 2
            self.canvas.create_oval(x - 10, y - 10, x + 10, y + 10,
                                    fill=fill, outline=outline, width=ow)
            tid = self.canvas.create_text(x, y - 22, text=f"{spot.spot_id}.{spot.name}",
                                          fill=COLORS["text"], font=("微软雅黑", 9))
            bbox = self.canvas.bbox(tid)
            rid = self.canvas.create_rectangle(bbox[0] - 4, bbox[1] - 2,
                                               bbox[2] + 4, bbox[3] + 2,
                                               fill="#ffffff", outline="")
            self.canvas.tag_lower(rid, tid)

        # 左上角标题与图例（白色底板，避免与节点标签重叠）
        self.canvas.create_rectangle(8, 8, 345, 64, fill="#ffffff", outline=COLORS["border"])
        self.canvas.create_text(16, 14, anchor="nw", text="遂宁市景点拓扑地图",
                                fill=COLORS["primary"], font=("微软雅黑", 13, "bold"))
        self.canvas.create_text(16, 40, anchor="nw", text="出行方式：",
                                fill=COLORS["muted"], font=("微软雅黑", 9))
        for index, method in enumerate(("步行", "公交车", "自驾")):
            x = 16 + 72 + index * 78
            self.canvas.create_line(x, 46, x + 22, 46, fill=METHOD_COLORS[method], width=3)
            self.canvas.create_text(x + 27, 46, anchor="w", text=method,
                                    fill=COLORS["text"], font=("微软雅黑", 9))

    # ---------- 查询 ----------
    def _query_paths(self) -> None:
        try:
            start, end = self.name_to_id[self.query_start.get()], self.name_to_id[self.query_end.get()]
            if start == end:
                raise ValueError("起点和终点不能相同")
            self.current_paths = self.path_tables[start].search(end)
            self.result_mode = "paths"
            self._show_paths()
        except KeyError:
            messagebox.showerror("查询错误", "请选择起点和终点")
        except ValueError as exc:
            messagebox.showerror("查询错误", str(exc))

    def _show_paths(self) -> None:
        if self.result_mode != "paths":
            return
        criterion = self.sort_criterion.get()
        if criterion == "默认顺序":
            self.current_paths.sort(key=default_path_sort_key)
        else:
            self.current_paths = sort_paths(self.current_paths, criterion)
        self.result.delete(0, tk.END)
        self.result.selection_clear(0, tk.END)
        for index, path in enumerate(self.current_paths, 1):
            names = " -> ".join(self.spots[spot_id].name for spot_id in path.spots)
            methods = "、".join(edge.method for edge in path.edges)
            self.result.insert(
                tk.END,
                f"{index}. {names} | {methods} | {path.distance:.1f}km | "
                f"{path.time:.0f}min | {path.cost:.1f}元 | {path.stop_count}个途经点")
        self.result.yview_moveto(0)
        # 自动高亮当前排序下的首条（最优）路径
        if self.current_paths:
            self.result.selection_set(0)
            self.result.activate(0)
            self._draw_map(self.current_paths[0])
            self.status.configure(
                text=f"共 {len(self.current_paths)} 条路径，已高亮第 1 条（{self.sort_criterion.get()}最优），单击列表可切换")
        else:
            self._draw_map(None)
            self.status.configure(text="未找到可达路径")

    def _select_result(self, _: object = None) -> None:
        selection = self.result.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx < len(self.current_paths) and self.current_paths[idx] is not None:
            self._draw_map(self.current_paths[idx])
            self.status.configure(text="已高亮所选路径")

    def _resort_current(self) -> None:
        """切换排序方式后，若当前显示的是全部路径结果则立即重排并高亮首条。"""
        if self.result_mode == "paths" and self.current_paths:
            self._show_paths()

    def _shortest_paths(self) -> None:
        if self.query_start.get() not in self.name_to_id:
            messagebox.showerror("查询错误", "请选择起点")
            return
        start = self.name_to_id[self.query_start.get()]
        self.result.delete(0, tk.END)
        self.result.selection_clear(0, tk.END)
        # current_paths 与列表框逐行对应：可点击行存 PathInfo，标题/不可达行存 None
        self.current_paths = []
        self.result_mode = "shortest"
        for title, weight in (("距离最短", lambda edge: edge.distance),
                              ("时间最短", lambda edge: edge.time),
                              ("费用最少", lambda edge: edge.cost)):
            _, previous = self.graph.dijkstra(start, weight)
            self.result.insert(tk.END, f"【{title}】")
            self.current_paths.append(None)
            for target in self.spots:
                if target == start:
                    continue
                path = rebuild_path(previous, start, target)
                if path is None:
                    self.result.insert(tk.END, f"  -> {self.spots[target].name}：不可达")
                    self.current_paths.append(None)
                else:
                    self.result.insert(tk.END,
                                       f"  -> {self.spots[target].name}："
                                       f"{path.distance:.1f}km/{path.time:.0f}min/{path.cost:.1f}元")
                    self.current_paths.append(path)
        self.result.yview_moveto(0)
        # 自动高亮首条可达路径
        first = next((i for i, p in enumerate(self.current_paths) if p is not None), None)
        if first is not None:
            self.result.selection_set(first)
            self.result.activate(first)
            self._draw_map(self.current_paths[first])
            self.status.configure(text="三类最优路径计算完成，已高亮首条，单击列表可切换")
        else:
            self._draw_map(None)
            self.status.configure(text="三类最优路径计算完成，无可达路径")


def main() -> None:
    root = tk.Tk()
    ScenicMapApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
