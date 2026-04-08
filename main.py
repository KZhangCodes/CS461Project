from city_agent import CityAgent
from city_graph import CityGraph
from grid import Grid
from agent import Agent
from gui import Visualiser

ALGORITHMS = ["bfs", "dfs", "iddfs", "best_first", "astar"]

def run_grid() -> None:
    size = int(input("Grid size N (default 10): ") or 10)
    grid = Grid(size=size)
    Visualiser(grid, Agent(grid)).run()

#loads city graph and prints neighbors
def run_city() -> None:
    graph = CityGraph("coordinates.csv", "Adjacencies.txt")
    print("Cities:", ", ".join(graph.all_cities()))
    start = input("Start city: ").strip()
    goal = input("Goal city: ").strip()
    print("Algorithms:", ", ".join(ALGORITHMS))
    algorithm = input("Algorithm (default bfs): ").strip() or "bfs"

    agent = CityAgent(graph, start, goal)
    gen = getattr(agent, algorithm)()

    #no animation yet
    event = None
    for event in gen:
        pass

    if event and event[0] == "done":
        path, states = event[1], event[2]
        if path:
            print(f"\nPath: {' -> '.join(path)}")
            print(f"Length: {len(path) - 1} | States explored: {states}")
        else:
            print(f"No path found, states explored: {states}")

def main():
    mode = input("Mode grid or city (default grid): ").strip() or "grid"
    if mode == "city":
        run_city()
    else:
        run_grid()

if __name__ == "__main__":
    main()

