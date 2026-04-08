import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Patch
from matplotlib.widgets import Button
from city_graph import CityGraph
from city_agent import CityAgent

ALGORITHMS = ["bfs", "dfs", "iddfs", "best_first", "astar"]

class CityVisualiser:
    INTERVAL_MS = 300

    def __init__(self, graph: CityGraph) -> None:
        self.graph = graph
        self.algorithm = ALGORITHMS[0] #default to first algorithm bfs
        self.start: str | None = None
        self.goal: str | None = None
        self._generator = None
        self._animation = None
        self._visited: set[str] = set()
        self._queue_set: set[str]  = set()
        self._path: list[str] = []
        self._search_done = False
        self._current_node: str | None = None
        self._click_count = 0 #first click start, second click goal
        self._algo_buttons: list[Button] = []
        self._build_window()

    #create figure, map axis, buttons and connects click event
    def _build_window(self) -> None:
        self.fig = plt.figure(figsize=(14, 9))
        self.ax_map = self.fig.add_axes([0.0, 0.12, 0.78, 0.88])
        self._build_algorithm_buttons()
        self._build_control_buttons()
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self._draw_map()
        self._update_status("Click start node")

    #create algorithm buttons
    def _build_algorithm_buttons(self) -> None:
        for i, algorithm in enumerate(ALGORITHMS):
            ax_btn = self.fig.add_axes([0.80, 0.82 - i * 0.1, 0.18, 0.07])
            btn = Button(ax_btn, algorithm.upper())

            def on_click(event, alg=algorithm) -> None:
                self._select_algorithm(alg)

            btn.on_clicked(on_click)
            self._algo_buttons.append(btn)

    #create play and restart button
    def _build_control_buttons(self) -> None:
        ax_start = self.fig.add_axes([0.80, 0.18, 0.18, 0.09])
        self._btn_start = Button(ax_start, "Play")
        self._btn_start.on_clicked(self._begin)
        ax_reset = self.fig.add_axes([0.80, 0.06, 0.18, 0.09])
        self._btn_reset = Button(ax_reset, "Restart")
        self._btn_reset.on_clicked(self._reset)

    #set active algorithm and highlight
    def _select_algorithm(self, algorithm: str) -> None:
        self.algorithm = algorithm
        for i, btn in enumerate(self._algo_buttons):
            btn.color = "green" if ALGORITHMS[i] == algorithm else "white"
        self.fig.canvas.draw_idle()

    #map clicks
    def _on_click(self, event) -> None:
        #ignore clicks outside map or both nodes selected
        if event.inaxes != self.ax_map or self._search_done or self._click_count >= 2:
            return
        clicked_city = self._nearest_city(event.xdata, event.ydata)
        if clicked_city is None:
            return
        if self._click_count == 0:
            self.start = clicked_city
            self._click_count = 1
            self._update_status(f"Start: {clicked_city} ")
        elif self._click_count == 1 and clicked_city != self.start:
            self.goal = clicked_city
            self._click_count = 2
            self._update_status(f"Start: {self.start}  Goal: {clicked_city} — Press start")
        self._draw_map()
        self.fig.canvas.draw_idle()

    #return city whose position is closest to click coords
    def _nearest_city(self, click_x: float, click_y: float) -> str | None:
        if click_x is None or click_y is None:
            return None
        closest_city = None
        closest_distance = float("inf")
        #compare squared distance to avoid sqrt
        for city, (latitude, longitude) in self.graph.positions.items():
            distance = (longitude - click_x) ** 2 + (latitude - click_y) ** 2
            if distance < closest_distance:
                closest_distance = distance
                closest_city = city
        return closest_city

    #creates the search geneartor and start animation loop
    def _begin(self, event) -> None:
        if self.start is None or self.goal is None:
            self._update_status("Select start and goal nodes")
            return
        if self._generator is not None: #stop double start
            return
        agent = CityAgent(self.graph, self.start, self.goal)
        self._generator = getattr(agent, self.algorithm)() #call selected algorithm
        self._animation = animation.FuncAnimation(self.fig, self._step, interval=self.INTERVAL_MS, cache_frame_data=False)
        self.fig.canvas.draw_idle()

    #stops animation and resets parameters
    def _reset(self, event) -> None:
        if self._animation:
            self._animation.event_source.stop()
        self.start = None
        self.goal = None
        self._generator = None
        self._animation = None
        self._visited = set()
        self._queue_set = set()
        self._path = []
        self._search_done = False
        self._current_node = None
        self._click_count = 0
        self._update_status("START")
        self._draw_map()
        self.fig.canvas.draw_idle()

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

    #draws edges between connected cities, path edges in orange
    def _draw_edges(self, ax, positions: dict, path_set: set) -> None:
        drawn_edges: set[frozenset[str]] = set()
        for city, neighbors in self.graph.edges.items():
            if city not in positions:
                continue
            for neighbor in neighbors:
                edge = frozenset({city, neighbor})
                #skip drawn edges, bidirectional so each pair show twice
                if edge in drawn_edges or neighbor not in positions:
                    continue
                drawn_edges.add(edge)
                city_lon, city_lat = positions[city][1], positions[city][0]
                neighbor_lon, neighbor_lat = positions[neighbor][1], positions[neighbor][0]
                on_path = city in path_set and neighbor in path_set
                ax.plot([city_lon, neighbor_lon], [city_lat, neighbor_lat], color="orange" if on_path else "gray", lw=2.5 if on_path else 0.8, zorder=1)

    #city nodes as points with name labels
    def _draw_nodes(self, ax, positions: dict) -> None:
        for city, (latitude, longitude) in positions.items():
            node_size = 250 if city in (self.start, self.goal) else 180
            ax.scatter(longitude, latitude, s=node_size, color=self._node_color(city), zorder=3, edgecolors="black", linewidths=0.6)
            ax.annotate(city.replace("_", " "), (longitude, latitude), fontsize=7, ha="center", va="bottom", zorder=4) #remove underscore on city text

    #color legend and algorithm label
    def _draw_legend(self, ax) -> None:
        legend_items = [Patch(color="green", label="Start"),Patch(color="red", label="Goal"), Patch(color="darkorange", label="Current"),
                        Patch(color="yellow", label="Frontier"), Patch(color="lightblue", label="Visited"), Patch(color="orange", label="Path"),
                        Patch(facecolor="white", edgecolor="black", label="Unvisited"),]
        ax.legend(handles=legend_items, loc="upper left", fontsize=8)
        ax.text(0.01, 0.01, f"Algorithm: {self.algorithm.upper()}", transform=ax.transAxes, fontsize=9, va="bottom")

    #map draw and clear
    def _draw_map(self) -> None:
        ax = self.ax_map
        ax.cla()
        positions = self.graph.positions
        path_set = set(self._path)
        self._draw_edges(ax, positions, path_set)
        self._draw_nodes(ax, positions)
        self._draw_legend(ax)
        ax.axis("off")

    #draw and reclear of status message
    def _update_status(self, message: str) -> None:
        self.fig.texts.clear()
        self.fig.text(0.39, 0.04, message, ha="center", fontsize=9)
        self.fig.canvas.draw_idle()

    #called each animation frame, advances search and redraws map
    def _step(self, frame: int) -> None:
        if self._search_done or self._generator is None:
            return
        try:
            event = next(self._generator)
        except StopIteration:
            return

        if event[0] == "step":
            current_city, frontier_cities = event[1], event[2]
            self._current_node = current_city
            self._visited.add(current_city)
            self._queue_set = set(frontier_cities) #update frontier

        elif event[0] == "done":
            path, states_explored = event[1], event[2]
            self._path = path or []
            self._queue_set.clear()
            self._search_done = True
            self._animation.event_source.stop()
            self._update_status(f"Path length: {len(path) - 1}  |  States explored: {states_explored}" if path else f"No path found.  States explored: {states_explored}")

        self._draw_map()

    def run(self) -> None:
        plt.show()