from PIL import Image, ImageColor, ImageDraw
from random import randint, choice, seed as randomseed
from typing import *
from math import hypot
from queue import Queue
from dataclasses import dataclass


class Constant:
    manhattonian_steps = ((0, 1), (1, 0), (-1, 0), (0, -1))
    chebyshev_steps = ((0, 1), (1, 0), (-1, 0), (0, -1), (-1, -1), (-1, 1), (1, -1), (1, 1))


class RegionAlgorithm:
    def randomized(width: int, height: int, regions: int) -> List[Tuple[int, int]]:
        """Return regions that are entirely random."""
        points = []
        while len(points) != regions:
            p = (randint(0, width - 1), randint(0, height - 1))

            if p in points:
                continue

            points.append(p)

        return points

    def uniform(width: int, height: int, regions: int) -> List[Tuple[int, int]]:
        """Return regions that attempt to be somewhat uniform. Picks """
        k = 10
        points = []
        while len(points) != regions:
            best_p = None
            d_max = 0

            for _ in range(k * len(points) + 1):
                p = (randint(0, width - 1), randint(0, height - 1))

                if p in points:
                    continue

                if len(points) == 0:
                    best_p = p
                    break

                d_min = float('inf')
                for x, y in points:
                    d = hypot(p[0]-x, p[1]-y)

                    if d < d_min:
                        d_min = d

                if d_min > d_max:
                    d_max = d_min
                    best_p = p

            if best_p is None:
                continue

            points.append(best_p)

        return points


class DistanceAlgorithm:
    def euclidean(width: int, height: int,
            region_centers: List[Tuple[int, int]], image: List[List[int]]):
        """Calculate the image regions using euclidean distance."""

        for x in range(width):
            for y in range(height):
                d_min = float('inf')

                for region in region_centers:
                    nx, ny = region
                    d = hypot(nx-x, ny-y)

                    if d < d_min:
                        d_min = d
                        image[x][y] = id(region)

    def manhattonian(*args):
        """Calculate the image regions using manhattonian distance."""
        DistanceAlgorithm._bfs(*args, Constant.manhattonian_steps)

    def chebyshev(*args):
        """Calculate the image regions using chebyshev distance."""
        DistanceAlgorithm._bfs(*args, Constant.chebyshev_steps)

    def _bfs(width: int, height: int,
            region_centers: List[Tuple[int, int]], image: List[List[int]],
            steps):
        """Calculate the image regions using some sort of BFS."""
        queue = Queue()

        for region in region_centers:
            queue.put((*region, id(region)))

        while not queue.empty():
            x, y, i = queue.get()

            for dx, dy in steps:
                xn, yn = x + dx, y + dy

                if not 0 <= xn < width or not 0 <= yn < height:
                    continue

                if image[xn][yn] == None:
                    image[xn][yn] = i
                    queue.put((xn, yn, i))


class Utilities:
    def error(message, q=True):
        print(f"\u001b[38;5;1mERROR:\u001b[0m {message}", flush=True)

        if q:
            quit()

    def info(message):
        print(f"\u001b[38;5;11mINFO:\u001b[0m {message}", flush=True)

    def success(message):
        print(f"\u001b[38;5;2mSUCCESS:\u001b[0m {message}", flush=True)

def generate(
        path: str,
        regions: int,
        colors: List[Union[Tuple[int, int, int], str]],
        width: int = 1920,
        height: int = 1080,
        region_algorithm = RegionAlgorithm.uniform,
        distance_algorithm = DistanceAlgorithm.euclidean,
        no_same_adjacent_colors: bool = False,
        seed = None,
):
    # check for correct region count
    if width * height < regions:
        Utilities.error("Not enough pixels for the number of regions.")

    # possibly seed the random algorithm
    if seed is not None:
        randomseed(seed)

    Utilities.info("Calculating region centers.")
    region_centers = region_algorithm(width, height, regions)

    image = [[None] * height for _ in range(width)]
    Utilities.info("Calculating region areas.")
    distance_algorithm(width, height, region_centers, image)

    # possibly convert string colors to tuples
    i = 0
    while i < len(colors):
        if type(colors[i]) == str:
            color = colors[i].strip("#")

            colors[i] = (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))

        i += 1

    # either assign colors randomly, or calculate the chromatic number and assign them then
    if not no_same_adjacent_colors:
        Utilities.info("Assigning region colors.")
        region_colors = {id(region): choice(colors) for region in region_centers}
    else:
        Utilities.info("Assigning region colors such that no two adjacent regions have the same color.")
        from pulp import LpProblem, LpVariable, LpMinimize, lpSum, PULP_CBC_CMD

        edges = set()

        mapping = {}
        n = 0

        for x in range(width):
            for y in range(height):
                for xd, yd in Constant.manhattonian_steps:
                    xn, yn = x + xd, y + yd

                    if not 0 <= xn < width or not 0 <= yn < height:
                        continue

                    i1, i2 = image[x][y], image[xn][yn]

                    if i1 < i2:
                        if i1 not in mapping:
                            n += 1
                            mapping[n] = i1
                            mapping[i1] = n

                        if i2 not in mapping:
                            n += 1
                            mapping[n] = i2
                            mapping[i2] = n

                        edges.add((mapping[i1], mapping[i2]))

        edges = list(edges)
        model = LpProblem(sense=LpMinimize)

        chromatic_number = LpVariable(name="chromatic number", cat='Integer')
        variables = [[LpVariable(name=f"x_{i}_{j}", cat='Binary') \
                      for i in range(n)] for j in range(n)]

        for i in range(n):
            model += lpSum(variables[i]) == 1
        for u, v in edges:
            for color in range(n):
                model += variables[u - 1][color] + variables[v - 1][color] <= 1
        for i in range(n):
            for j in range(n):
                model += chromatic_number >= (j + 1) * variables[i][j]

        model += chromatic_number

        status = model.solve(PULP_CBC_CMD(msg=False))

        if chromatic_number.value() > len(colors):
            error("Not enough colors to color without adjacent areas having the same one!")

        region_colors = {mapping[variable + 1]: colors[color]
                for variable in range(n)
                for color in range(n)
                if variables[variable][color].value() == 1}

    pil_image = Image.new("RGB", (width, height))

    for x in range(width):
        for y in range(height):
            pil_image.putpixel((x, y), region_colors[image[x][y]])

    pil_image.save(path, "PNG")
    Utilities.success(f"File saved to {path}")
