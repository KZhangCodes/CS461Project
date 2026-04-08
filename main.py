import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from city_graph import CityGraph
from city_gui import CityVisualiser
from grid import Grid
from agent import Agent
from gui import Visualiser

def launch() -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axis("off")
    ax.text(0.5, 0.72, "AI Search Visualiser", ha="center", va="center", fontsize=16, transform=ax.transAxes)
    ax.text(0.5, 0.58, "Select mode", ha="center", va="center", fontsize=10, transform=ax.transAxes)

    #grid button
    ax_grid = fig.add_axes([0.15, 0.25, 0.3, 0.15])
    btn_grid = Button(ax_grid, "Grid")

    def open_grid(event) -> None:
        _launch_grid(fig)
    btn_grid.on_clicked(open_grid)

    #city graph button
    ax_city = fig.add_axes([0.55, 0.25, 0.3, 0.15])
    btn_city = Button(ax_city, "City graph")

    def open_city(event) -> None:
        _launch_city(fig)
    btn_city.on_clicked(open_city)

    plt.show()

#closes launcher, opens grid default 10
def _launch_grid(launcher_fig) -> None:
    plt.close(launcher_fig)
    grid = Grid(size=10)
    Visualiser(grid, Agent(grid)).run()

#closes launcher, loads city graph
def _launch_city(launcher_fig) -> None:
    plt.close(launcher_fig)
    graph = CityGraph("coordinates.csv", "Adjacencies.txt")
    CityVisualiser(graph).run()

if __name__ == "__main__":
    launch()

