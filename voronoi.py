from PIL import Image, ImageColor, ImageDraw
from random import randint, choice, seed as randomseed
from typing import *
from math import hypot, sqrt, atan2
from queue import Queue
from dataclasses import dataclass
from enum import Enum
from shapely import geometry
import svgwrite
import os
import shapely

class OutputFormat(Enum):
    PNG = 1
    SVG = 2


class ColorAlgorithm(Enum):
    random           = 1
    no_adjacent_same = 2
    least_possible   = 3


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
        """Return regions that attempt to be somewhat uniform."""
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
    def euclidean(*args):
        """Calculate the image regions (up to a distance) using euclidean distance."""
        DistanceAlgorithm._set_each_point(*args, lambda x, y, xn, yn: hypot(xn-x, yn-y))

    def manhattan(*args):
        """Calculate the image regions using manhattan distance."""
        DistanceAlgorithm._set_each_point(*args, lambda x, y, xn, yn: abs(xn-x) + abs(yn-y))

    def euclidean45degrees(*args):
        """Calculate the image regions using euclidean, but allow only lines in 45 degree increments."""
        DistanceAlgorithm._set_each_point(*args, lambda x, y, xn, yn: sqrt(2 * min(abs(xn-x), abs(yn-y)) ** 2) + abs(abs(xn-x) - abs(yn-y)))

    def chebyshev(*args):
        """Calculate the image regions using chebyshev distance."""
        DistanceAlgorithm._set_each_point(*args, lambda x, y, xn, yn: min(abs(xn-x), abs(yn-y)) + abs(abs(xn-x) - abs(yn-y)))

    def _set_each_point(width: int, height: int,
            region_centers: List[Tuple[int, int]], image: List[List[int]],
            d_limit: int, f: Callable[[int, int, int, int], float]):
        """Calculate the image regions (up to a distance) using the provided metric."""
        for x in range(width):
            for y in range(height):
                d_min = float('inf')

                for region in region_centers:
                    xn, yn = region
                    d = f(x, y, xn, yn)

                    if d < d_min:
                        d_min = d

                        if d <= d_limit:
                            image[x][y] = id(region)

class Utilities:
    def error(message, q=True):
        print(f"\u001b[38;5;1mERROR:\u001b[0m {message}", flush=True)

        if q:
            quit()

    def info(message):
        print(f"\u001b[38;5;11mINFO:\u001b[0m {message}", flush=True)

    def success(message):
        print(f"\u001b[38;5;2mSUCCESS:\u001b[0m {message}", flush=True)

    def hex_to_tuple(color: str):
        color = color.strip("#")
        return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))

    def get_different_adjacent_colors(width, height, image, colors, color_algorithm):
        from pulp import LpProblem, LpVariable, LpMinimize, lpSum, PULP_CBC_CMD

        edges = set()

        mapping = {}
        n = 0

        for x in range(width):
            for y in range(height):
                for xd, yd in ((0, 1), (1, 0), (-1, 0), (0, -1)):
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

        if color_algorithm == ColorAlgorithm.least_possible:
            model += chromatic_number
        else:
            model += chromatic_number == len(colors)

        status = model.solve(PULP_CBC_CMD(msg=False))

        if chromatic_number.value() > len(colors):
            Utilities.error("Not enough colors to color without adjacent areas having the same one!")

        return {mapping[variable + 1]: colors[color]
                for variable in range(n)
                for color in range(n)
                if variables[variable][color].value() == 1}

    def add_border(border_color, border_size, read_image, write_image, width, height):
        r = border_size // 2

        if type(border_color) == str:
            border_color = Utilities.hex_to_tuple(border_color)

        for x in range(width):
            for y in range(height):
                for dx, dy in ((0, 1), (1, 0)):
                    xn, yn = x + dx, y + dy

                    if not 0 <= xn < width or not 0 <= yn < height:
                        continue

                    if read_image[x][y] != read_image[xn][yn]:
                        draw = ImageDraw.Draw(write_image)
                        draw.ellipse((x-r, y-r, x+r, y+r), fill=(*border_color,0))


def generate(
        path: str,
        regions: int,
        colors: List[Union[Tuple[int, int, int], str]],
        width: int = 1920,
        height: int = 1080,
        region_algorithm = RegionAlgorithm.uniform,
        distance_algorithm = DistanceAlgorithm.euclidean,
        color_algorithm = ColorAlgorithm.random,
        seed = None,
        border_size = 0,
        border_color = "#FFFFFF",
        animate_fill = False,
        animation_background = "#FFFFFF",
        output_format = OutputFormat.PNG,
):
    # possibly seed the random algorithm
    if seed is not None:
        randomseed(seed)

    if type(regions) == list:
        Utilities.info("Region centers provided, skipping generation.")

        # flip vertically!
        region_centers = [(int(center[0] * width), int(height - center[1] * height)) for center in regions]
    else:
        # check for correct region count
        if width * height < regions:
            Utilities.error("Not enough pixels for the number of regions.")

        Utilities.info("Calculating region centers.")
        region_centers = region_algorithm(width, height, regions)

    if output_format == OutputFormat.SVG:
        svg_document = svgwrite.Drawing(filename = path + ".svg", size = (f"{width}px", f"{height}px"))

        # for each region, calculate its polygon
        for p1 in region_centers:
            # take each line and create a half plane
            polygon = geometry.Polygon([(0, 0), (width, 0), (width, height), (0, height)])
            for p2 in region_centers:
                if p1 is p2:
                    continue

                corners = [(0, 0), (width, 0), (width, height), (0, height)]

                x1, y1 = p1
                x2, y2 = p2

                # the line is vertical
                if (y1 == y2):
                    p = [(x1, y1), (x1, y2)]

                    a = None

                # the line is not vertical
                else:
                    # TODO: other metrics!
                    a = - (x2 - x1) / (y2 - y1)
                    b = (y1 + y2) / 2 - a * (x1 + x2) / 2

                    f = lambda x: a * x + b

                    L = (0, f(0))
                    U = (-b / a, 0)
                    R = (width, f(width))
                    D = ((height - b) / a, height)

                    p = []

                    if 0 <= L[1] <= height:
                        p.append(L)
                    if 0 <= R[1] <= height:
                        p.append(R)
                    if 0 <= D[0] <= width:
                        p.append(D)
                    if 0 <= U[0] <= width:
                        p.append(U)

                side = lambda x, y: (a is None and x < x1) or ((f(x) < y) == (f(x1) < y1))

                p += [(x, y) for x, y in corners if side(x, y)]

                if len(p) <= 2:
                    continue

                # sort them by planar coordinates form the region
                # the polygon is convex so there is no problem with this
                p = sorted(p, key = lambda p: atan2(p1[0] - p[0], p1[1] - p[1]))
                polygon = polygon.intersection(geometry.Polygon(p))

            # TODO: colors!
            svg_document.add(svgwrite.shapes.Polygon(polygon.exterior.coords[:-1], fill=("rgb" + str(region_colors[p1]))))

        svg_document.save()

    if output_format == OutputFormat.PNG:
        image = [[None] * height for _ in range(width)]
        Utilities.info("Calculating region areas.")
        distance_algorithm(width, height, region_centers, image, float("inf"))

        # possibly convert string colors to tuples
        i = 0
        while i < len(colors):
            if type(colors[i]) == str:
                colors[i] = Utilities.hex_to_tuple(colors[i])

            i += 1

        # either assign colors randomly, or calculate the chromatic number and assign them then
        if color_algorithm == ColorAlgorithm.random:
            Utilities.info("Assigning region colors.")
            region_colors = {id(region): choice(colors) for region in region_centers}
        else:
            Utilities.info("Assigning region colors such that no two adjacent regions have the same color.")
            region_colors = Utilities.get_different_adjacent_colors(width, height, image, colors, color_algorithm)

        # the original, full image (without borders)
        pil_image = Image.new("RGB", (width, height))
        for x in range(width):
            for y in range(height):
                pil_image.putpixel((x, y), region_colors[image[x][y]])

        if border_size != 0:
            Utilities.add_border(border_color, border_size, image, pil_image, width, height)

        if animate_fill:
            if not os.path.exists(path):
                os.makedirs(path)

            d = 1

            if type(animation_background) == str:
                animation_background = Utilities.hex_to_tuple(animation_background)

            while True:
                animation_image = [[None] * height for _ in range(width)]
                distance_algorithm(width, height, region_centers, animation_image, d)

                animation_pil_image = Image.new("RGB", (width, height))

                for x in range(width):
                    for y in range(height):
                        animation_pil_image.putpixel((x, y), animation_background if animation_image[x][y] is None else region_colors[image[x][y]])

                if border_size != 0:
                    Utilities.add_border(border_color, border_size, animation_image, animation_pil_image, width, height)

                animation_path = os.path.join(path, f"{d}.png")

                animation_pil_image.save(animation_path, "PNG")
                Utilities.success(f"Animation image saved to {animation_path}")

                d += 1

                if image == animation_image:
                    Utilities.success(f"Done!")
                    break

        else:
            pil_image.save(path, "PNG")
            Utilities.success(f"Image saved to {path}!")

generate(
    path = "1",
    regions = 8,
    colors = [(0, 0, 0), (15, 15, 15), (23, 23, 23), (30, 30, 30)],
    output_format = OutputFormat.SVG,
)
