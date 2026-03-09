import matplotlib.pyplot as plt
import matplotlib.animation as animation
from grid import OBSTACLE, START, GOAL

#x/y positions for each node in tree
def _layout_tree(root_key, children, depth_limit=30):
    positions, edges = {}, []

    #place node at midpoint of its horizontal , then divide among children
    def assign(node, depth, left, right):
        if depth > depth_limit:
            return
        positions[node] = ((left + right) / 2, -depth)
        child_nodes = children.get(node, [])
        if not child_nodes or depth == depth_limit:
            return
        width = (right - left) / len(child_nodes)
        for i, child in enumerate(child_nodes):
            child_left = left + i * width
            assign(child, depth + 1, child_left, child_left + width)
            edges.append((node, child))

    assign(root_key, 0, 0.0, 1.0)
    return positions, edges

class Visualiser:
    INTERVAL_MS = 80

    def __init__(self, grid, agent):
        self.grid, self.agent = grid, agent
        self.grid_size = grid.size
        #cache start/goal as tuples for drawing
        self.start_key = (grid.start.row, grid.start.col)
        self.goal_key  = (grid.goal.row,  grid.goal.col)
        self._generator = self._animation = None
        self._visited, self._frontier, self._path = set(), set(), []
        self._search_done = False
        #parent map for path reconstruction, children map for layout
        self._tree_parent   = {}
        self._tree_children = {self.start_key: []}
        self._tree_current  = None
        self.fig, (self.ax_grid, self.ax_tree) = plt.subplots(1, 2, figsize=(12, 6))
        self.fig.suptitle("Click to start", fontsize=10)

        def on_click(event):
            self._begin()

        self.fig.canvas.mpl_connect("button_press_event", on_click)
        self._draw_grid()
        self._draw_tree()

    #convert current path list into a set of tuples
    @property
    def _path_set(self):
        return {(node.row, node.col) for node in self._path}

    def _begin(self):
        if self._generator is not None:
            return
        self._generator = self.agent.bfs()
        self._animation = animation.FuncAnimation(self.fig, self._step, interval=self.INTERVAL_MS, cache_frame_data=False)
        self.fig.suptitle("")
        self.fig.canvas.draw_idle()

    #resolves display color of a cell based on state
    def _cell_color(self, cell_value, cell_pos, path_set):
        if cell_value == OBSTACLE:
            return "black"
        if cell_value == START:
            return "green"
        if cell_value == GOAL:
            return "red"
        if cell_pos in path_set:
            return "orange"
        if cell_pos in self._frontier:
            return "yellow"
        if cell_pos in self._visited:
            return "lightblue"
        return "white"

    #redraws 2d grid and coloring cell according to current search state
    def _draw_grid(self):
        ax, size = self.ax_grid, self.grid_size
        ax.cla()
        path_set = self._path_set
        for row in range(size):
            for col in range(size):
                color = self._cell_color(self.grid.grid[row][col], (row, col), path_set)
                ax.add_patch(plt.Rectangle((col, size - row - 1), 1, 1, facecolor=color, edgecolor="gray", linewidth=0.5))
        ax.set_xlim(0, size)
        ax.set_ylim(0, size)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title("2D Grid")

    #redraws search tree and highlights edges/nodes of final path
    def _draw_tree(self):
        ax = self.ax_tree
        ax.cla()
        path_set = self._path_set
        positions, edges = _layout_tree(self.start_key, self._tree_children)
        if not positions:
            ax.axis("off"); return

        #draw edges, orange if both endpoints are in final path
        for parent, child in edges:
            if parent in positions and child in positions:
                x0, y0 = positions[parent]
                x1, y1 = positions[child]
                on_path = parent in path_set and child in path_set
                ax.plot([x0, x1], [y0, y1],
                        color="orange" if on_path else "gray",
                        lw=2.0 if on_path else 0.7, zorder=1)

        #draw nodes and color by type
        for node, (x, y) in positions.items():
            if node == self.start_key:
                color = "green"
            elif node == self.goal_key:
                color = "red"
            elif node in path_set:
                color = "orange"
            elif node == self._tree_current:
                color = "darkorange"
            else:
                color = "lightblue"
            ax.scatter(x, y, s=120, color=color, zorder=3)
        ax.set_title("Search Tree"); ax.axis("off")

    #adds new frontier nodes to tree structure
    def _update_tree(self, current_key, frontier):
        for node in frontier:
            node_key = (node.row, node.col)
            if node_key not in self._tree_parent and node_key != self.start_key:
                self._tree_parent[node_key] = current_key
                self._tree_children.setdefault(current_key, []).append(node_key)
                self._tree_children.setdefault(node_key, [])

    #advances bfs by one step and redraws both views
    def _step(self, frame):
        if self._search_done or self._generator is None:
            return
        try:
            event = next(self._generator)
        except StopIteration:
            return

        if event[0] == "step":
            current_node, queued_nodes = event[1], event[2]
            current_key = (current_node.row, current_node.col)
            self._tree_current = current_key
            self._visited.add(current_key)
            self._queue_set = {(node.row, node.col) for node in queued_nodes}
            self._update_tree(current_key, queued_nodes)

        elif event[0] == "done":
            path, states_explored = event[1], event[2]
            self._path = path or []
            self._queue_set.clear()
            self._search_done = True
            self._animation.event_source.stop()
            self.fig.suptitle(
                f"Path length: {len(path) - 1} | States explored: {states_explored}"
                if path else f"States explored: {states_explored}", fontsize=10)

        self._draw_grid()
        self._draw_tree()

    def run(self):
        plt.tight_layout()
        plt.show()





