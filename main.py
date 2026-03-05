from grid import Grid
from gui import draw_grid

def main():

    size = input("Grid size N: ")

    if size == "":
        size = 10
    else:
        size = int(size)

    grid = Grid(size=size)
    draw_grid(grid)

if __name__ == "__main__":
    main()

