# Voronoi
A simple Python library for generationg various kinds of Voronoi diagrams.

To install, run:
```
git clone https://github.com/xiaoxiae/Voronoi.git
pip install -r requirements.txt
```

## Examples

```py
from voronoi import generate

generate(
    path = "1.png",
    width = 3840,
    height = 2160,
    regions = 70,
    colors = [(0, 0, 0), (15, 15, 15), (23, 23, 23), (30, 30, 30)],
    no_same_adjacent_colors = True,
)
```

![First example.](./examples/1.png)

```
from voronoi import generate

generate(
    path = "2.png",
    regions = 30,
    colors = ["#91db57", "#57d3db", "#5770db", "#a157db", "#db57b2"],
)
```

![Second example.](./examples/2.png)
