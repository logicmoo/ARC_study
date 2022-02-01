from typing import TypeAlias, TypedDict
import matplotlib
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
import numpy as np


class PlotDef(TypedDict):
    grid: np.ndarray
    name: str


Layout: TypeAlias = list[list[PlotDef]]

color_map = matplotlib.colors.ListedColormap(  # type: ignore
    [
        "#888888",
        "#000000",
        "#0074D9",
        "#FF2222",
        "#2ECC40",
        "#FFDC00",
        "#AAAAAA",
        "#F012BE",
        "#FF8C00",
        "#7FDBFF",
        "#870C25",
        "#444444",
    ]
)
norm = matplotlib.colors.Normalize(vmin=-1, vmax=10)  # type: ignore


def plot_color_map() -> Figure:
    # -1: light grey, (for Cutout)
    # 0:black, 1:blue, 2:red, 3:greed, 4:yellow,
    # 5:gray, 6:magenta, 7:orange, 8:sky, 9:brown
    # 10: dark grey, (for Transparency)
    fig = plt.figure(figsize=(3, 1), dpi=200)
    plt.imshow([list(range(11))], cmap=color_map, norm=norm)
    plt.xticks(list(range(11)))
    plt.yticks([])
    return fig


def plot_layout(layout: Layout, scale: float = 1.0, show_axis: bool = True) -> Figure:
    """Plot a 2D array of grids specified by a Layout.

    A jagged Layout (uneven row lengths) is handled in this function.
    """
    M, N = len(layout), max([len(row) for row in layout])
    fig, axs = plt.subplots(M, N, squeeze=False, figsize=(2 * N * scale, 2 * M * scale))
    for r_idx, row in enumerate(layout):
        for c_idx in range(N):
            curr_axes = axs[r_idx][c_idx]
            if c_idx >= len(row):
                curr_axes.axis("off")
                continue
            args = row[c_idx]
            _add_plot(args["grid"], curr_axes, args["name"], show_axis)
    plt.tight_layout()
    return fig


def plot_grid(grid: np.ndarray, title: str = "", show_axis: bool = True) -> Figure:
    fig, axes = plt.subplots(1, 1, figsize=(4, 4))
    _add_plot(grid, axes, title=title, show_axis=show_axis)
    return fig


def _add_plot(
    grid: np.ndarray, axes: Axes, title: str = "", show_axis: bool = True
) -> None:
    """Plot an ARC grid, uses axes if supplied."""
    axes.set_title(title, {"fontsize": 8})
    if not show_axis:
        axes.axis("off")
    axes.imshow(grid, cmap=color_map, norm=norm)
    axes.set_yticks(list(range(grid.shape[0])))
    axes.set_xticks(list(range(grid.shape[1])))
