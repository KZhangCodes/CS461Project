import random
from dataclasses import dataclass

EMPTY = 0
OBSTACLE = 1
START = 2
GOAL = 3

@dataclass
class Position:
    row: int
    col: int

class Grid:
    #initialize grid, obstacles and places start/goal
    def __init__(self, size=10, obstacle_sparsity=(0.2, 0.3)):
        self.size = size
        self.grid = [[EMPTY for _ in range(size)] for _ in range(size)]
        self._place_obstacles(obstacle_sparsity)
        self.start = self._random_free_cell()
        self.goal = self._random_free_cell()
        self.grid[self.start.row][self.start.col] = START
        self.grid[self.goal.row][self.goal.col] = GOAL

    #random placement of obstacles in sparsity range 20-30%
    def _place_obstacles(self, obstacle_sparsity):
        ratio = random.uniform(*obstacle_sparsity)
        total_cells = self.size * self.size
        obstacle_count = int(total_cells * ratio)

        placed = 0
        while placed < obstacle_count:
            row = random.randrange(self.size)
            col = random.randrange(self.size)
            if self.grid[row][col] == EMPTY:
                self.grid[row][col] = OBSTACLE
                placed += 1

    def _random_free_cell(self):
        while True:
            row = random.randrange(self.size)
            col = random.randrange(self.size)
            if self.grid[row][col] == EMPTY:
                return Position(row, col)

    #returns valid neighboring cells NSEW that are not obstacles
    def neighbors(self, pos):
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        result = []
        for row_offset, col_offset in directions:
            neighbor_row = pos.row + row_offset
            neighbor_col = pos.col + col_offset
            if 0 <= neighbor_row < self.size and 0 <= neighbor_col < self.size:
                if self.grid[neighbor_row][neighbor_col] != OBSTACLE:
                    result.append(Position(neighbor_row, neighbor_col))

        return result



