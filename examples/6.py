from voronoi import *

generate(
    path = "6.png",
    regions = 20,
    distance_algorithm = [DistanceAlgorithm.manhattan, DistanceAlgorithm.euclidean],
    colors = ["#ff7b00", "#ff9500", "#ffb700", "#ffea00"],
    color_algorithm = ColorAlgorithm.no_adjacent_same,
    border_size = 10,
)
