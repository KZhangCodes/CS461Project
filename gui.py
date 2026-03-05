import matplotlib.pyplot as plt
import numpy as np

EMPTY = 0
OBSTACLE = 1
START = 2
GOAL = 3

def draw_grid(grid_object):
    #grid list into NumPy array
    grid = np.array(grid_object.grid)
    size = grid_object.size
    figure, axis = plt.subplots()
    #iterate through each cell
    for row_index in range(size):
        for col_index in range(size):
            if grid[row_index][col_index] == OBSTACLE: #grid type by color
                cell_color = "black"
            elif grid[row_index][col_index] == START:
                cell_color = "green"
            elif grid[row_index][col_index] == GOAL:
                cell_color = "red"
            else:
                cell_color = "white"

            #square representing cells, flipped row index so row 0 appears at top
            cell_rectangle = plt.Rectangle((col_index, size - row_index -1), 1, 1, facecolor=cell_color, edgecolor="gray")
            axis.add_patch(cell_rectangle)

    #grid helpers
    axis.set_xlim(0, size)
    axis.set_ylim(0, size)
    axis.set_aspect("equal")
    axis.axis("off")

    plt.show()





