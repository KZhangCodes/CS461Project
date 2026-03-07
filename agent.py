from grid import Position, OBSTACLE

class Agent:
    def __init__(self, grid):
        self.grid = grid
        self.position = grid.start
    #neighbor search
    def search(self):
        neighbors = self.grid.neighbors(self.position)
        return {
            "current": self.position,
            "neighbors": neighbors
        }
    #move to valid neighbor
    def move(self, new_position):

        valid_neighbors = self.grid.neighbors(self.position)

        for neighbor in valid_neighbors:
            if neighbor.row == new_position.row and neighbor.col == new_position.col:
                self.position = new_position
                return True

        return False