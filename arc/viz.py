from typing import Any, TypeAlias, TypedDict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from arc.board import Board
from arc.definitions import Constants as cst
from arc.link import ObjectDelta
from arc.object import Object
from arc.scene import Scene
from arc.task import Task
from arc.types import Grid
from arc.util import logger

log = logger.fancy_logger("Viz", level=20)


class PlotDef(TypedDict, total=False):
    grid: Grid
    name: str
    primitive: str


Layout: TypeAlias = list[list[PlotDef]]


def plot(item: Any, **kwargs: Any) -> Figure:
    match item:
        case Object():
            return plot_grid(item.grid, **kwargs)
        case Board(current=""):
            return plot_grid(item.raw.grid, **kwargs)
        case Board(current=_):
            return plot_layout(tree_layout(item.rep), **kwargs)
        case Scene(dist=-1):
            return plot_layout(scene_layout(item), **kwargs)
        case Scene(dist=dist):
            log.info(f"Distance {dist}")
            return plot_layout(match_layout(item), **kwargs)
        case Task():
            return plot_layout(task_layout(item), **kwargs)
        case _:
            log.warning(f"Unsupported class for plotting: {item.__class__.__name__}")
            return plt.figure()


def tree_layout(obj: Object, max_dots: int = 5) -> Layout:
    plot_items: list[Object | str] = [obj]
    layout: Layout = []
    while plot_items:
        layout_line: list[PlotDef] = []
        for item in plot_items:
            if isinstance(item, str):
                layout_line.append({"primitive": item})
            else:
                layout_line.append({"grid": item.grid, "name": item.id})
        layout.append(layout_line)

        new_plot_items: list[Object | str] = []
        plot_objs: list[Object] = list(filter(lambda x: isinstance(x, Object), plot_items))  # type: ignore
        for idx, item in enumerate(plot_objs):
            if new_plot_items and idx > 0 and item.children:
                new_plot_items.append("divider")
            dot_ct = 0
            for kid in item.children:
                if kid.category == "Dot":
                    if kid.color == cst.NULL_COLOR:
                        continue
                    if dot_ct < max_dots:
                        new_plot_items.append(kid)
                    elif dot_ct == max_dots:
                        new_plot_items.append("ellipsis")
                    dot_ct += 1
                else:
                    new_plot_items.append(kid)
        plot_items = new_plot_items
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
    for link in scene.link_map.values():
        if isinstance(link, ObjectDelta):
            inp, out, trans = link.left, link.right, link.transform
            left: PlotDef = {"grid": inp.grid, "name": inp.category}
            name = ", ".join([action.__name__ for action in trans.actions])
            right: PlotDef = {"grid": out.grid, "name": name}
            layout.append([left, right])
    return layout


color_map = matplotlib.colors.ListedColormap(  # type: ignore
    [
        "#000000",  # 0: black
        "#0074D9",  # 1: blue
        "#FF2222",  # 2: red
        "#2ECC40",  # 3: green
        "#FFDC00",  # 4: yellow
        "#AAAAAA",  # 5: gray
        "#F012BE",  # 6: magenta
        "#FF8C00",  # 7: orange
        "#7FDBFF",  # 8: sky
        "#870C25",  # 9: brown
        "#444444",  # 10: dark grey, (for Transparency)
        "#888888",  # 11: light grey, (for Cutout)
    ]
)
norm = matplotlib.colors.Normalize(vmin=-1, vmax=cst.N_COLORS)  # type: ignore


def plot_color_map() -> Figure:
    fig = plt.figure(figsize=(3, 1), dpi=200)
    plt.imshow([list(range(cst.N_COLORS))], cmap=color_map, norm=norm)  # type: ignore
    plt.xticks(list(range(cst.N_COLORS)))  # type: ignore
    plt.yticks([])  # type: ignore
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
            curr_axes: Axes = axs[r_idx][c_idx]  # type: ignore
            if c_idx >= len(row):
                curr_axes.axis("off")  # type: ignore
                continue
            _add_plot(curr_axes, row[c_idx], show_axis)
    plt.tight_layout()
    return fig


def plot_grid(grid: Grid, title: str = "", show_axis: bool = True) -> Figure:
    fig, axes = plt.subplots(1, 1, figsize=(4, 4))
    plot_def: PlotDef = {"grid": grid, "name": title}
    _add_plot(axes, plot_def, show_axis=show_axis)
    return fig


def _add_plot(axes: Axes, plot_def: PlotDef, show_axis: bool = True) -> None:
    """Plot an ARC grid, uses axes if supplied."""
    axes.set_title(plot_def.get("name"), {"fontsize": 8})
    if not show_axis:
        axes.axis("off")
    if plot_def.get("primitive") == "divider":
        _divider(axes)
    elif plot_def.get("primitive") == "ellipsis":
        _ellipsis(axes)
    grid = plot_def.get("grid")
    if grid is not None:
        axes.imshow(grid, cmap=color_map, norm=norm)
        axes.set_yticks(list(range(grid.shape[0])))
        axes.set_xticks(list(range(grid.shape[1])))


def _divider(axes: Axes) -> None:
    axes.axis("off")
    axes.axvline(x=0.5, lw=5, ls="--", color="black")  # type: ignore


def _ellipsis(axes: Axes) -> None:
    axes.axis("off")
    axes.scatter([0, 0.2, 0.4], [0, 0, 0], color="black")  # type: ignore
