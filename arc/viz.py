from typing import Any, TypeAlias, TypedDict
from uuid import UUID

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from pyvis.network import Network  # type: ignore (no stub file)

from arc.actions import Actions
from arc.board import Board
from arc.definitions import Constants as cst
from arc.link import ObjectDelta
from arc.node import Node, VarNode
from arc.node_selection import SelectionNode
from arc.object import Object
from arc.scene import Scene
from arc.solution import Solution
from arc.task import Task
from arc.template import CommonProperties, StructureDef
from arc.types import BaseObjectPath, Grid
from arc.util import logger

log = logger.fancy_logger("Viz", level=20)


class PlotDef(TypedDict, total=False):
    grid: Grid
    name: str
    primitive: str


Layout: TypeAlias = list[list[PlotDef]]

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
    """Plot a bar of the colors used."""
    fig = plt.figure(figsize=(3, 1), dpi=200)
    plt.imshow([list(range(cst.N_COLORS))], cmap=color_map, norm=norm)  # type: ignore
    plt.xticks(list(range(cst.N_COLORS)))  # type: ignore
    plt.yticks([])  # type: ignore
    return fig


def plot(item: Any, **kwargs: Any) -> Figure:
    """Plot a class from ARC, based on the information present.

    Object: Always simply plot its grid.
    Board: Plot the grid, unless a 'current representation' is defined, then
        plot a hierarchical breakdown of the decomposition
    Scene: Plot side-by-side input and output grids, unless a 'distance' is
        defined, then plot the links determined for the Scene.
    Task: Always plot all cases and tests, inputs on top, outputs on bottom.
    """
    match item:
        case Object():
            return plot_grid(item.grid, **kwargs)
        case Board(current=""):
            return plot_grid(item.raw.grid, **kwargs)
        case Board(current=_):
            return plot_layout(tree_layout(item.rep), **kwargs)
        case Scene(current=""):
            return plot_layout(scene_layout(item), **kwargs)
        case Scene(current=_):
            return plot_layout(link_layout(item), **kwargs)
        case Task():
            return plot_layout(task_layout(item), **kwargs)
        case _:
            log.warning(f"Unsupported class for plotting: {item.__class__.__name__}")
            return plt.figure()


def tree_layout(obj: Object, max_dots: int = 5) -> Layout:
    """Recursively plot an Object and its children."""
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
    """Plot the Task's Scene inputs along the top, outputs on the bottom."""
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
    """Plot the input and output board side-by-side"""
    inp_obj, out_obj = scene.input.rep, scene.output.rep
    left: PlotDef = {"grid": inp_obj.grid, "name": "Input"}
    right: PlotDef = {"grid": out_obj.grid, "name": "Output"}
    return [[left, right]]


def link_layout(scene: Scene) -> Layout:
    """Plot linked Objects from the input and output."""
    layout: Layout = []
    for link in scene.link_map.values():
        if isinstance(link, ObjectDelta):
            inp, out, trans = link.left, link.right, link.transform
            left: PlotDef = {"grid": inp.grid, "name": inp.category}
            arrow: PlotDef = {"primitive": "rarrow", "name": f"{trans}"}
            right: PlotDef = {"grid": out.grid, "name": out.category}
            layout.append([left, arrow, right])
    return layout


def plot_layout(layout: Layout, scale: float = 1.0) -> Figure:
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
                # Empty plot
                curr_axes.axis("off")  # type: ignore
                continue
            _add_plot(curr_axes, row[c_idx])
    plt.tight_layout()
    return fig


def _node_label(node: Node) -> str:
    bold_name = f"<b>{node.name}</b>"
    if isinstance(node, SelectionNode) and not node.specs:
        args = "All"
    else:
        args = "\n".join(node.specs)
    return f"{bold_name}\n{args}"


def _structure_label(name: str, props: CommonProperties) -> str:
    bold_name = f"<b>{name}</b>"
    args: list[str] = []
    for name, val in props.items():
        if len(name) == 1:
            name = str(Actions.map[name])
        if name == "color":
            val = cst.cname.get(val, "?")  # type: ignore
        args.append(f"{name}: {val}")
    argstr = "\n".join(args)
    return f"{bold_name}\n{argstr}"


def add_template(network: Network, solution: Solution, colors: dict[UUID, str]) -> None:
    structure = solution.template.structure
    base_level = solution.terminus.level + 1

    queue: list[tuple[BaseObjectPath, StructureDef]] = [(tuple(), structure)]
    network.add_node(  # type: ignore
        n_id="()",
        label=_structure_label("Structure Root", structure["props"]),
        shape="box",
        level=base_level,
        font={"multi": "html", "size": 20},
        color="lightgrey",
        borderWidth=2,
    )
    while queue:
        path, node = queue.pop(0)
        for idx, child_dict in enumerate(node["children"]):
            child_path = path + (idx,)
            queue.append((child_path, child_dict))
            network.add_node(  # type: ignore
                n_id=str(child_path),
                label=_structure_label(str(child_path), child_dict["props"]),
                shape="box",
                level=base_level + len(child_path),
                font={"multi": "html", "size": 20},
                borderWidth=2,
                color="lightgrey",
            )
            network.add_edge(  # type: ignore
                source=str(path),
                to=str(child_path),
                arrows={"to": {"enabled": False}},
                color="black",
            )

    # Add edges from Terminus to structure
    for node_id, path_set in solution.terminus.path_map.items():
        for path in path_set:
            dashes: bool = path.property is not None
            color: str = colors.get(node_id, "black")
            network.add_edge(  # type: ignore
                source=str(solution.terminus.uid),
                to=str(path.base),
                arrows={"to": {"enabled": True}},
                dashes=dashes,
                color=color,
                smooth={"type": "curvedCW", "roundness": 0.4},
            )


def plot_solution(
    solution: Solution,
    filename: str = "solution_plot.html",
    notebook: bool = False,
    height: int = 600,
    width: int = 1200,
) -> Any:
    """Create a Pyvis graph for the Task Solution and Template.

    The Solution graph showing each Node is created first, and the
    'add_template' call generates the Task Output template.
    """

    network = Network(
        notebook=notebook,
        height=f"{height}px",
        width=f"{width}px",
        directed=True,
        layout=True,
    )

    # Tweaking Pyvis is challenging, being a mid-fidelity wrapper on VisJs.
    # physics.hierarchicalRepulsion.avoidOverlap sets a level of node
    # repulsion so they usually no longer overlap.
    network.set_options(  # type: ignore
        """
      const options = {
        "layout": { "hierarchical": {} },
        "physics": { "hierarchicalRepulsion": { "avoidOverlap": 1.0 } }
      }
    """
    )

    insertion_colors: dict[UUID, str] = {}
    for idx, uid in enumerate(solution.terminus.path_map):
        insertion_colors[uid] = cst.cname[idx + 1]

    for uid, node in solution.nodes.items():
        network.add_node(  # type: ignore
            n_id=str(uid),
            label=_node_label(node),
            shape="box",
            level=node.level,
            font={"multi": "html", "size": 20},
            borderWidth=2,
        )

    for uid, node in solution.nodes.items():
        for child_node in node.children:
            arrow_type: str = "arrow"
            if node == child_node.secondary:
                arrow_type = "box"

            dashes: bool = isinstance(node, VarNode)
            color: str = insertion_colors.get(uid, "black")

            network.add_edge(  # type: ignore
                source=str(uid),
                to=str(child_node.uid),
                arrows={"to": {"enabled": True, "type": arrow_type}},
                endPointOffset={"to": 50},
                dashes=dashes,
                color=color,
                smooth="straightCross",
            )

    # Show the Output Structure template for the ARC Task solution
    add_template(network, solution, insertion_colors)

    return network.write_html(filename, notebook=notebook)  # type: ignore


def plot_grid(grid: Grid, title: str = "") -> Figure:
    """Plot a grid (2D array) by itself"""
    fig, axes = plt.subplots(1, 1, figsize=(4, 4))
    plot_def: PlotDef = {"grid": grid, "name": title}
    _add_plot(axes, plot_def)
    return fig


def _add_plot(axes: Axes, plot_def: PlotDef) -> None:
    """Plot a plot definition (grid or primitive & title) on supplied axes."""
    axes.set_title(plot_def.get("name"), {"fontsize": 10})
    axes.axis("off")
    if plot_def.get("primitive") == "divider":
        _divider(axes)
    elif plot_def.get("primitive") == "ellipsis":
        _ellipsis(axes)
    elif plot_def.get("primitive") == "rarrow":
        _rarrow(axes)
    grid = plot_def.get("grid")
    if grid is not None:
        edgecolors = None
        if grid.shape[0] < 15 or grid.shape[1] < 15:
            edgecolors = "grey"
        axes.pcolormesh(grid[::-1], cmap=color_map, norm=norm, edgecolors=edgecolors)  # type: ignore
        axes.set_aspect("equal")


def _divider(axes: Axes) -> None:
    """Vertical dashed lines, acting as a divider."""
    axes.axis("off")
    axes.axvline(x=0.5, lw=5, ls="--", color="black")  # type: ignore


def _rarrow(axes: Axes) -> None:
    """Right facting arrow."""
    axes.axis("off")
    axes.axhline(y=0.5, lw=3, ls="--", marker=">", ms=10, color="black", clip_on=False)  # type: ignore


def _ellipsis(axes: Axes) -> None:
    """Three dots, used as an ellipsis."""
    axes.axis("off")
    axes.scatter([0, 0.2, 0.4], [0, 0, 0], color="black")  # type: ignore
