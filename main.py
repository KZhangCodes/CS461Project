from grid import Grid
from gui import draw_grid
from agent import Agent

def main():

    size = input("Grid size N: ")

    if size == "":
        size = 10
    else:
        size = int(size)

    grid = Grid(size=size)
    agent = Agent(grid)
    search = agent.search()

    print("Agent start:", search["current"])
    print("Neighbors:", search["neighbors"])

    draw_grid(grid)

if __name__ == "__main__":
    main()

