from voronoi import *

generate(
    path = "3.png",
    regions = 50,
    colors = ["#78c9b1", "#3eab71", "#27904d", "#006127"],
    no_same_adjacent_colors = True,
    distance_algorithm = DistanceAlgorithm.manhattan,
)
