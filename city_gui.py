import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QCheckBox, QPushButton, QButtonGroup, QFrame, QSizePolicy)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Figuremap
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from city_graph import CityGraph
from city_agent import CityAgent
from city_benchmark import show_benchmark_window

ALGORITHMS = ["bfs", "dfs", "iddfs", "best_first", "astar"]

class CityVisualiser(QMainWindow):
    INTERVAL_MS = 300

    def __init__(self, graph: CityGraph) -> None:
        self.app = QApplication.instance() or QApplication(sys.argv)
        super().__init__()
        self.graph = graph
        self.algorithm = ALGORITHMS[0]
        self.start: str | None = None
        self.goal: str | None = None
        self._generator = None
        self._visited: set[str] = set()
        self._queue_set: set[str] = set() #current frontier
        self._path: list[str] = []
        self._search_done = False
        self._current_node: str | None = None
        self._click_count = 0 #first click start, second click goal
        self._benchmark_algo_selection: set[str] = {"bfs"}
        self._timer = QTimer()
        self._timer.timeout.connect(self._step)
        self._build_window()

    #build maps and connect click
    def _build_map(self) -> Figuremap:
        self.fig = Figure(figsize=(10, 7))
        self.ax_map = self.fig.add_axes([0.0, 0.0, 1.0, 1.0])
        self.map = Figuremap(self.fig)
        self.map.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.map.mpl_connect("button_press_event", self._on_click)
        return self.map

    #build main window, embeds map and sidebar
    def _build_window(self) -> None:
        self.setWindowTitle("City Search Visualiser")
        self.resize(1200, 750)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._build_map(), stretch=1)
        layout.addWidget(self._build_sidebar())
        self._draw_map()

    #radio buttons and checkboxes
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(_section_label("Single run"))
        self._radio_group = QButtonGroup(self) #only one radio button selected

        for algorithm in ALGORITHMS:
            radio_btn = QRadioButton(algorithm.upper())
            radio_btn.setChecked(algorithm == self.algorithm)
            radio_btn.toggled.connect(self._make_radio_slot(algorithm))
            self._radio_group.addButton(radio_btn)
            layout.addWidget(radio_btn)

        layout.addLayout(self._build_play_row())
        layout.addWidget(_divider())
        layout.addWidget(_section_label("Benchmark"))
        self._check_boxes: dict[str, QCheckBox] = {}

        for algorithm in ALGORITHMS:
            check_box = QCheckBox(algorithm.upper())
            check_box.setChecked(algorithm in self._benchmark_algo_selection)
            check_box.stateChanged.connect(self._make_check_slot(algorithm))
            self._check_boxes[algorithm] = check_box
            layout.addWidget(check_box)

        bench_btn = QPushButton("Run benchmark")
        bench_btn.clicked.connect(self._run_benchmark)
        layout.addWidget(bench_btn)
        layout.addStretch()
        self._status_label = QLabel("Click start node")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)
        return sidebar

    #play and restart buttons
    def _build_play_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        btn_play = QPushButton("Play")
        btn_play.clicked.connect(self._begin)
        btn_restart = QPushButton("Restart")
        btn_restart.clicked.connect(self._reset)
        row.addWidget(btn_play)
        row.addWidget(btn_restart)
        return row

    #slot funtion that sets the active algorithm on radio button selection
    def _make_radio_slot(self, algorithm: str):
        def slot(checked: bool) -> None:
            if checked:
                self.algorithm = algorithm
        return slot

    #add or remove an algorithm from benchmark
    def _make_check_slot(self, algorithm: str):
        def slot(state: int) -> None:
            if state:
                self._benchmark_algo_selection.add(algorithm)
            else:
                self._benchmark_algo_selection.discard(algorithm)
        return slot

    #benchmark window
    def _run_benchmark(self) -> None:
        if not self._nodes_selected():
            return
        if not self._benchmark_algo_selection:
            self._update_status("Select at least one to benchmark")
            return
        selected_algorithms = [alg for alg in ALGORITHMS if alg in self._benchmark_algo_selection]
        show_benchmark_window(self.graph, self.start, self.goal, selected_algorithms)

    #map clicks
    def _on_click(self, event) -> None:
        #ignore clicks outside map or both nodes selected
        if event.inaxes != self.ax_map or self._search_done or self._click_count >= 2:
            return
        city = self._nearest_city(event.xdata, event.ydata)
        if city is None:
            return
        if self._click_count == 0:
            self.start = city
            self._click_count = 1
            self._update_status(f"Start: {city}")
        elif self._click_count == 1 and city != self.start:
            self.goal = city
            self._click_count = 2
            self._update_status(f"Start: {self.start}  Goal: {city} — Press Play")
        self._draw_map()
        self.map.draw_idle()

    #create search generator for selected algorithm and start animation
    def _begin(self) -> None:
        if not self._nodes_selected() or self._generator is not None:
            return
        agent = CityAgent(self.graph, self.start, self.goal)
        self._generator = getattr(agent, self.algorithm)()
        self._timer.start(self.INTERVAL_MS)

    #stops animation and resets parameters
    def _reset(self) -> None:
        self._timer.stop()
        self.start = None
        self.goal = None
        self._generator = None
        self._visited = set()
        self._queue_set = set()
        self._path = []
        self._search_done = False
        self._current_node = None
        self._click_count = 0
        self._update_status("Click start node")
        self._draw_map()
        self.map.draw_idle()

    #called each animation frame, advances search and redraws map
    def _step(self) -> None:
        if self._search_done or self._generator is None:
            return
        event = next(self._generator, None)
        if event is None:
            return

        match event[0]:
            case "step":
                self._current_node = event[1]
                self._visited.add(event[1])
                self._queue_set = set(event[2])
            case "done":
                self._on_search_done(*event[1:])

        self._draw_map()
        self.map.draw_idle()

    #handles done event from generator, stores the path and shows summary
    def _on_search_done(self, path, states_explored, elapsed_ms, peak_kb, heuristic_stats) -> None:
        self._path = path or []
        self._queue_set.clear()
        self._search_done = True
        self._timer.stop()
        if path:
            depth = len(path) - 1
            total_cost = heuristic_stats.get("total_cost") if heuristic_stats else None
            self._update_status("")
            self._draw_summary_panel(depth, states_explored, elapsed_ms, peak_kb, total_cost, heuristic_stats)
        else:
            self._update_status(f"No path found.  States: {states_explored}  |  Time: {elapsed_ms:.1f} ms")

    #node selection validator
    def _nodes_selected(self) -> bool:
        if self.start is None or self.goal is None:
            self._update_status("Select start and goal nodes")
            return False
        return True

    #return city whose position is closest to click coords
    def _nearest_city(self, x: float, y: float) -> str | None:
        if x is None or y is None:
            return None

        def key(city: str) -> float:
            latitude, longitude = self.graph.positions[city]
            return (longitude - x) ** 2 + (latitude - y) ** 2
        return min(self.graph.positions, key=key)

    def _update_status(self, message: str) -> None:
        self._status_label.setText(message)

    #returns display color of city based on current search state
    def _node_color(self, city: str) -> str:
        if city == self.start:
            return "green"
        if city == self.goal:
            return "red"
        if city in self._path:
            return "orange"
        if city == self._current_node:
            return "darkorange"
        if city in self._queue_set:
            return "yellow"
        if city in self._visited:
            return "lightblue"
        return "white"

    #map draw and clear
    def _draw_map(self) -> None:
        self.ax_map.cla()
        path_set = set(self._path)
        self._draw_edges(path_set)
        self._draw_nodes()
        self._draw_legend()
        self.ax_map.axis("off")

    #draws edges between connected cities, path edges in orange
    def _draw_edges(self, path_set: set) -> None:
        drawn_edges: set[frozenset[str]] = set()
        for city, neighbors in self.graph.edges.items():
            for neighbor in neighbors:
                edge = frozenset({city, neighbor})
                if edge in drawn_edges or neighbor not in self.graph.positions or city not in self.graph.positions: #skip drawn edges, bidirectional so each pair show tice
                    continue
                drawn_edges.add(edge)
                city_latitude, city_longitude = self.graph.positions[city]
                neighbor_latitude, neighbor_longitude = self.graph.positions[neighbor]
                on_path = city in path_set and neighbor in path_set
                self.ax_map.plot([city_longitude, neighbor_longitude], [city_latitude, neighbor_latitude], color="orange" if on_path else "gray", lw=2.5 if on_path else 0.8, zorder=1)

    #city nodes as points with name labels
    def _draw_nodes(self) -> None:
        for city, (latitude, longitude) in self.graph.positions.items():
            size = 250 if city in (self.start, self.goal) else 180
            self.ax_map.scatter(longitude, latitude, s=size, color=self._node_color(city), zorder=3, edgecolors="black", linewidths=0.6)
            self.ax_map.annotate(city.replace("_", " "), (longitude, latitude), fontsize=7, ha="center", va="bottom", zorder=4) #remove underscore on city text

    #legend
    def _draw_legend(self) -> None:
        legend_items = ([Patch(color=color, label=label) for color, label in
                        [("green", "Start"), ("red", "Goal"), ("darkorange", "Current"),
                        ("yellow", "Frontier"), ("lightblue", "Visited"), ("orange", "Path"),]] +
                        [Patch(facecolor="white", edgecolor="black", label="Unvisited")])
        self.ax_map.legend(handles=legend_items, loc="upper left", fontsize=8)
        self.ax_map.text(0.01, 0.01, f"Algorithm: {self.algorithm.upper()}", transform=self.ax_map.transAxes, fontsize=9, va="bottom")

    #summary panel as dialogue box
    def _draw_summary_panel(self, depth: int, states_explored: int, elapsed_ms: float, peak_kb: float, total_cost: float | None, heuristic_stats: dict | None) -> None:
        lines = [f"Path length: {depth}", f"Time: {elapsed_ms:.1f} ms", f"Memory: {peak_kb:.0f} kb", f"Expanded: {states_explored}",]
        if total_cost is not None:
            lines.append(f"Cost: {total_cost:.2f}")
        if heuristic_stats:
            lines += [f"heuristic goal: {heuristic_stats['at_goal']:.2f}", f"heuristic max: {heuristic_stats['max']:.2f}", f"heuristic avg: {heuristic_stats['avg']:.2f}"]
        dialog = QMainWindow(self)
        dialog.setWindowTitle("Summary")
        widget = QWidget()
        dialog.setCentralWidget(widget)
        label = QLabel("\n".join(lines))
        label.setFont(QFont("Courier", 10))
        QVBoxLayout(widget).addWidget(label)
        dialog.adjustSize()
        dialog.show()

    def run(self) -> None:
        self.show()
        self.app.exec_()

def _section_label(text: str) -> QLabel:
    label = QLabel(f"<i>{text}</i>")
    label.setStyleSheet("font-size: 11px; color: gray;")
    return label

def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line