from typing import Any, TypeAlias, TypedDict

import matplotlib
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
import numpy as np

from arc.object import Object
from arc.scene import Scene
from arc.task import Task
from arc.util import logger

log = logger.fancy_logger("Viz", level=20)


class PlotDef(TypedDict):
    grid: np.ndarray
    name: str


Layout: TypeAlias = list[list[PlotDef]]


def plot(item: Any, **kwargs: Any) -> Figure:
    match item:
        case Object(history=[]):
            return plot_grid(item.grid, **kwargs)
        case Object(history=hist):
            return plot_layout(tree_layout(item), **kwargs)
        case Scene(dist=-1):
            return plot_layout(scene_layout(item), **kwargs)
        case Scene(dist=dist):
            log.info(f"Distance {item.dist}")
            return plot_layout(match_layout(item), **kwargs)
        case Task():
            return plot_layout(task_layout(item), **kwargs)
        case _:
            log.warning(f"Unsupported class for plotting: {item.__class__.__name__}")


def tree_layout(obj: Object) -> Layout:
    objs = [obj]
    layout: Layout = []
    while objs:
        layout.append([{"grid": obj.grid, "name": obj._id} for obj in objs])
        objs = [
            kid for obj in objs for kid in obj.children if not kid.category == "Dot"
        ]
    return layout


def task_layout(task: Task) -> Layout:
    layout: Layout = [[], []]
    for scene_idx, scene in enumerate(task.cases):
        layout[0].append(
            {"grid": scene.input.rep.grid, "name": f"Case {scene_idx}: Input"}
        )
        layout[1].append(
            {"grid": scene.output.rep.grid, "name": f"Case {scene_idx}: Output"}
        )
    for scene_idx, scene in enumerate(task.tests):
        layout[0].append(
            {"grid": scene.input.rep.grid, "name": f"Test {scene_idx}: Input"}
        )
        layout[1].append(
            {"grid": scene.output.rep.grid, "name": f"Test {scene_idx}: Output"}
        )
    return layout


def scene_layout(scene: Scene) -> Layout:
    inp_obj, out_obj = scene.input.rep, scene.output.rep
    left: PlotDef = {"grid": inp_obj.grid, "name": "Input"}
    right: PlotDef = {"grid": out_obj.grid, "name": "Output"}
    return [[left, right]]


def match_layout(scene: Scene) -> Layout:
    layout: Layout = []
    for delta in scene._path:
        inp, out, trans = delta.right, delta.left, delta.transform
        left: PlotDef = {"grid": inp.grid, "name": inp.category}
        right: PlotDef = {"grid": out.grid, "name": str(trans.items())}
        layout.append([left, right])
    return layout


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
    if not layout:
        return plt.figure()
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
