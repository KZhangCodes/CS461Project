from city_graph import CityGraph
from grid import Grid
from agent import Agent
from gui import Visualiser

ALGORITHM = ["bfs", "dfs", "iddfs", "best_first", "astar"]

def run_grid() -> None:
    size = int(input("Grid size N (default 10): ") or 10)
    grid = Grid(size=size)
    Visualiser(grid, Agent(grid)).run()

#loads city graph and prints neighbors
def run_city() -> None:
    graph = CityGraph("coordinates.csv", "Adjacencies.txt")
    print("Cities:", ", ".join(graph.all_cities()))
    city = input("Enter city for neighbors: ").strip()
    print(f"Neighbors of {city}: {graph.neighbors(city)}")

def main():
    mode = input("Mode grid or city (default grid): ").strip() or "grid"
    if mode == "city":
        run_city()
    else:
        run_grid()

if __name__ == "__main__":
    main()

