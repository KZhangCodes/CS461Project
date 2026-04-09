from collections import deque
import heapq
import time
import tracemalloc
import sys

sys.setrecursionlimit(10000)

type SearchEvent = tuple[str, str, list[str]] | tuple[str, list[str] | None, int]

#walks parent map from goal to start and reverses
def _reconstruct_path(parent: dict[str, str | None], goal: str) -> list[str]:
    path: list[str] = []
    current: str | None = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path

class CityAgent:
    #store graph, start, goal
    def __init__(self, graph, start: str, goal: str) -> None:
        self.graph = graph
        self.start = start
        self.goal = goal

    #uninformed bfs for shortest path on unweighted, level by level FIFO, similar to old agent bfs
    def bfs(self):
        tracemalloc.start()
        elapsed = 0.0 #track only computation time
        visited = {self.start}
        parent: dict[str, str | None] = {self.start: None}
        queue = deque([self.start])
        states_explored = 0
        nodes_generated = 1

        while queue:
            t0 = time.perf_counter() #start timer paused at yield
            current = queue.popleft() #takes oldest node
            states_explored += 1

            if current == self.goal:
                elapsed += (time.perf_counter() - t0)
                _current_mem, peak_bytes = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                yield "done", _reconstruct_path(parent, current), states_explored, elapsed * 1000, peak_bytes / 1024, None, nodes_generated
                return

            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current #record for path reconstruction
                    queue.append(neighbor)
                    nodes_generated += 1

            elapsed += (time.perf_counter() - t0) #accumulate before yielding
            yield "step", current, list(queue)
        _current_mem, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        yield "done", None, states_explored, elapsed * 1000, peak_bytes / 1024, None, nodes_generated

    #uninformed dfs, goes as deep as possible then backtrack with stack LIFO, doesnt guarantee shortest path
    def dfs(self):
        tracemalloc.start()
        elapsed = 0.0
        visited = {self.start}
        parent: dict[str, str | None] = {self.start: None}
        stack = [self.start]
        states_explored = 0
        nodes_generated = 1

        while stack:
            t0 = time.perf_counter()
            current = stack.pop() #takes newest node
            states_explored += 1

            if current == self.goal:
                elapsed += (time.perf_counter() - t0)
                _current_mem, peak_bytes = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                yield "done", _reconstruct_path(parent, current), states_explored, elapsed * 1000, peak_bytes / 1024, None, nodes_generated
                return

            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    stack.append(neighbor)
                    nodes_generated += 1

            elapsed += (time.perf_counter() - t0)
            yield "step", current, list(stack)
        _current_mem, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        yield "done", None, states_explored, elapsed * 1000, peak_bytes / 1024, None, nodes_generated

    #uninformed, runs depth limited search with increasing depth, _depth_limited_search kept separate to return result, path, state values back via yield from
    #reference for iddfs: https://www.geeksforgeeks.org/dsa/iterative-deepening-searchids-iterative-deepening-depth-first-searchiddfs/
    def iddfs(self):
        tracemalloc.start()
        elapsed = 0.0
        states_explored = 0
        nodes_generated = 0
        depth_limit = 0

        while True:
            result, path, states, iter_elapsed, iter_generated = yield from self._depth_limited_search(self.start, depth_limit)
            elapsed += iter_elapsed
            states_explored += states
            nodes_generated += iter_generated

            if result == "found":
                _current_mem, peak_bytes = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                yield "done", path, states_explored, elapsed * 1000, peak_bytes / 1024, None, nodes_generated
                return
            if result == "exhausted":
                _current_mem, peak_bytes = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                yield "done", None, states_explored, elapsed * 1000, peak_bytes / 1024, None, nodes_generated
                return
            depth_limit += 1

    #stops at depth limit, return a value via yield from
    def _depth_limited_search(self, start: str, depth_limit: int):
        parent: dict[str, str | None] = {start: None}
        stack = [(start, 0)]
        visited: set[str] = set()
        states_explored = 0
        any_remaining = False
        elapsed = 0.0
        nodes_generated = 1

        while stack:
            t0 = time.perf_counter()
            current, depth = stack.pop()
            if current in visited:
                elapsed += (time.perf_counter() - t0)
                continue
            visited.add(current)
            states_explored += 1

            if current == self.goal:
                elapsed += (time.perf_counter() - t0)
                return "found", _reconstruct_path(parent, current), states_explored, elapsed, nodes_generated

            if depth < depth_limit:
                for neighbor in self.graph.neighbors(current):
                    if neighbor not in visited:
                        if neighbor not in parent:
                            parent[neighbor] = current
                        stack.append((neighbor, depth + 1))
                        nodes_generated += 1
            else:
                any_remaining = True

            elapsed += (time.perf_counter() - t0)
            yield "step", current, [s[0] for s in stack]
        if any_remaining:
            return "cutoff", None, states_explored, elapsed, nodes_generated
        return "exhausted", None, states_explored, elapsed, nodes_generated

    #informed, expand with the lowest heuristic value, uses min heap so lowest heuristic node popped first
    def best_first(self):
        tracemalloc.start()
        elapsed = 0.0
        visited = {self.start}
        parent: dict[str, str | None] = {self.start: None}
        heap = [(self._chebyshev(self.start), self.start)]
        states_explored = 0
        heuristic_values: list[float] = [] #collects heuristic value popped
        nodes_generated = 1

        while heap:
            t0 = time.perf_counter()
            priority, current = heapq.heappop(heap)
            heuristic_values.append(priority)#pop lowest heuristic
            states_explored += 1

            if current == self.goal:
                elapsed += (time.perf_counter() - t0)
                _current_mem, peak_bytes = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                heuristic_stats = {"at_goal": priority, "max": max(heuristic_values), "avg": sum(heuristic_values) / len(heuristic_values)}
                yield "done", _reconstruct_path(parent, current), states_explored, elapsed * 1000, peak_bytes / 1024, heuristic_stats, nodes_generated
                return

            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    heapq.heappush(heap, (self._chebyshev(neighbor), neighbor))
                    nodes_generated += 1

            elapsed += (time.perf_counter() - t0)
            yield "step", current, [city for _priority, city in heap]
        _current_mem, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        yield "done", None, states_explored, elapsed * 1000, peak_bytes / 1024, None, nodes_generated

    #informed f(n) = g(n) + h(n), guarantees shortest path, nodes reexpanded if cheaper path found
    def astar(self):
        tracemalloc.start()
        elapsed = 0.0
        parent: dict[str, str | None] = {self.start: None}
        g_cost = {self.start: 0.0} #actual cost
        heap = [(self._euclidean(self.start), self.start)]
        visited: set[str] = set()
        states_explored = 0
        heuristic_values: list[float] = [] #collects heuristic value expanded
        nodes_generated = 1
        generated_set: set[str] = {self.start}

        while heap:
            t0 = time.perf_counter()
            f_score, current = heapq.heappop(heap)
            if current in visited:
                elapsed += (time.perf_counter() - t0) #count skipped nodes
                yield "step", current, [city for _priority, city in heap]
                continue
            visited.add(current)
            h = self._euclidean(current)
            heuristic_values.append(h)
            states_explored += 1

            if current == self.goal:
                elapsed += (time.perf_counter() - t0)
                _current_mem, peak_bytes = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                heuristic_stats = {"at_goal": h, "max": max(heuristic_values), "avg": sum(heuristic_values) / len(heuristic_values), "total_cost": g_cost[current]}
                yield "done", _reconstruct_path(parent, current), states_explored, elapsed * 1000, peak_bytes / 1024, heuristic_stats, nodes_generated
                return

            for neighbor in self.graph.neighbors(current):
                new_g = g_cost[current] + self.graph.distance(current, neighbor)
                if neighbor not in g_cost or new_g < g_cost[neighbor]:
                    g_cost[neighbor] = new_g #update if cheaper path found
                    parent[neighbor] = current
                    heapq.heappush(heap, (new_g + self._euclidean(neighbor), neighbor))
                    if neighbor not in generated_set:
                        generated_set.add(neighbor)
                        nodes_generated += 1

            elapsed += (time.perf_counter() - t0)
            yield "step", current, [city for _priority, city in heap]
        _current_mem, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        yield "done", None, states_explored, elapsed * 1000, peak_bytes / 1024, None, nodes_generated

    #euclidean heuristic for astar
    def _euclidean(self, city: str) -> float:
        return self.graph.distance(city, self.goal)

    #chebyshev distance heuristic for best_first
    #reference: https://www.geeksforgeeks.org/machine-learning/chebyshev-distance/
    def _chebyshev(self, city: str) -> float:
        latitude1, longitude1 = self.graph.positions[city]
        latitude2, longitude2 = self.graph.positions[self.goal]
        return max(abs(latitude1 - latitude2), abs(longitude1 - longitude2))




