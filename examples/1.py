from voronoi import *

generate(
    path = "1.png",
    width = 3840,
    height = 2160,
    regions = 70,
    colors = [(0, 0, 0), (15, 15, 15), (23, 23, 23), (30, 30, 30)],
    no_same_adjacent_colors = True,
)
