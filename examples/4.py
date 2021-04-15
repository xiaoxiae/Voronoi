from voronoi import *

generate(
    path = "4.png",
    regions = 50,
    colors = ["#1d63db", "#155ad0", "#0c4dbd", "#10459f"],
    no_same_adjacent_colors = True,
    distance_algorithm = DistanceAlgorithm.chebyshev,
    border_size = 20,
)
