from voronoi import *

generate(
    path = "4.png",
    regions = 50,
    colors = ["#1d63db", "#155ad0", "#0c4dbd", "#10459f"],
    distance_algorithm = DistanceAlgorithm.chebyshev,
    border_size = 20,
    border_color = "#093987",
    color_algorithm = ColorAlgorithm.no_adjacent_same,
)
