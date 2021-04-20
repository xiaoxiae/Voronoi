from voronoi import *

generate(
    path = "5.png",
    regions = 30,
    colors = ["#ffbec6", "#ffa4b4", "#ff7a92", "#ff5270", "#ff1e44"],
    distance_algorithm=DistanceAlgorithm.euclidean45degrees,
    color_algorithm = ColorAlgorithm.no_adjacent_same,
)
