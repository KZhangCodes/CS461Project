from collections import deque
from grid import Position

#walks parent map from goal back to start, then reverse to get path
def _reconstruct_path(parent, goal_node):
    path = []
    key = (goal_node.row, goal_node.col)
    while key is not None:
        row, col = key
        path.append(Position(row, col))
        previous = parent[key]
        key = (previous.row, previous.col) if previous else None
    path.reverse()
    return path

class Agent:
    def __init__(self, grid):
        self.grid = grid

    #level by level grid exploration, yield to allow animation
    def bfs(self):
        start = self.grid.start
        goal = self.grid.goal
        visited = {(start.row, start.col)}
        parent = {(start.row, start.col): None}
        queue = deque([start])
        states_explored = 0

        while queue:
            current = queue.popleft()
            states_explored += 1

            #when goal reached, reconstruct final path
            if (current.row, current.col) == (goal.row, goal.col):
                yield "done", _reconstruct_path(parent, current), states_explored
                return

            #add unvisited neighbors to queue
            for neighbor in self.grid.neighbors(current):
                neighbor_key = (neighbor.row, neighbor.col)
                if neighbor_key not in visited:
                    visited.add(neighbor_key)
                    parent[neighbor_key] = current
                    queue.append(neighbor)

            yield "step", current, list(queue)
        yield "done", None, states_explored
