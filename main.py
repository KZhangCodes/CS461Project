from grid import Grid
from agent import Agent
from gui import Visualiser

def main():
    size = int(input("Grid size N: ") or 10)

    grid = Grid(size=size)
    agent = Agent(grid)
    Visualiser(grid, agent).run()

if __name__ == "__main__":
    main()

