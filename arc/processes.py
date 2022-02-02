from typing import Any
import numpy as np
from abc import ABC, abstractmethod
from arc.generator import Generator
from arc.types import Point, PointList, Position

from arc.util import logger
from arc.grid_methods import color_connect, point_filter
from arc.definitions import Constants as cst
from arc.object import Object

log = logger.fancy_logger("Processes", level=30)


class Process(ABC):
    # NOTE: After adding in the context functionality, this could manifest in
    # parametrized instantion of decomposition processes.
    def __init__(self):
        pass

    def test(self, obj: Object) -> bool:
        """Check whether we believe we should run this process."""
        return True

    def repair(self, input: Object, output: Object) -> Object | None:
        """Repair any inconsistencies between input and output."""
        if input == output:
            return output

        log.debug(f"Patching {output} -> {output}")
        # TODO: For now, assume we can't fix missing points
        missing_locs = input.points.keys() - output.points.keys()
        if missing_locs:
            log.debug("  Missing output points during patch")
            return None

        extra_locs = output.points.keys() - input.points.keys()
        if extra_locs:
            cut_points = [(*loc, cst.NEGATIVE_COLOR) for loc in extra_locs]
            log.debug(f"  Cutting {len(cut_points)} points as patch")
            return self.add_layer(output, cut_points, "Cut")

        # Some colors must be different between input and output
        recolor_pts = []
        for loc, color in input.points.items():
            if output.points[loc] != color:
                recolor_pts.append((*loc, color))
        log.debug(f"  Recoloring {len(recolor_pts)} points as patch")
        return self.add_layer(output, recolor_pts, "Reco")

    def add_layer(self, output: Object, points: PointList, tag: str) -> Object:
        out = output.spawn(anchor=(0, 0, output.color))
        layer = Object.from_points(points)
        layer.traits["finished"] = True
        layer.traits["decomp"] = tag
        container = Object(*output.loc, children=[out, layer])
        container.traits["decomp"] = output.traits["decomp"]
        container.traits["finished"] = output.traits["finished"]
        return container

    @abstractmethod
    def run(self, obj: Object) -> Object | None:
        pass

    def info(self, obj: Object) -> None:
        log.debug(f"Running {self.__class__.__name__} on {obj._id}")

    def fail(self, message: str) -> None:
        log.debug(f"  ...failed: {message}")

    def success(self, obj: Object, message: str = "") -> None:
        msg_str = f"({message})" if message else ""
        log.debug(f"  ...finished: {(obj.props)} props {msg_str}")


class SeparateColor(Process):
    def test(self, obj: Object) -> bool:
        return len(obj.c_rank) > 1

    def run(self, obj: Object) -> Object:
        """Improves representation by combining points of like colors"""
        self.info(obj)
        color = obj.c_rank[0][0]

        match_pts, other_pts = point_filter(obj.points, color)
        match = Object.from_points(match_pts)
        other = Object.from_points(other_pts)
        candidate = Object(*obj.loc, children=[match, other])
        candidate.traits["decomp"] = f"SC{color}"
        candidate.traits["finished"] = True
        self.success(candidate)
        return candidate


class MakeBase(Process):
    def run(self, obj: Object) -> Object | None:
        self.info(obj)
        # NOTE: This currently assumes a black background if black is present
        # which should be altered later to be more data-driven.
        if 0 in [item[0] for item in obj.c_rank]:
            color = 0
        # Select a color to use, based on area covered by the color
        else:
            color = obj.c_rank[0][0]

        # Create a Generator based on the grid size
        codes = []
        rows, cols = obj.grid.shape
        if cols > 1:
            codes.append(f"C{cols - 1}")
        if rows > 1:
            codes.append(f"R{rows - 1}")
        generator = Generator.from_codes(codes) if codes else None

        # For a single color present, this simplifies to a single line/rect
        if len(obj.c_rank) == 1:
            candidate = Object(*obj.loc, color, generator=generator)
            candidate.traits["decomp"] = f"MB{color}"
            candidate.traits["finished"] = True
            candidate = self.repair(obj, candidate)
            if candidate:
                self.success(candidate, "single color")
            return candidate

        # Split off the base color from the "front matter"
        _, front_points = point_filter(obj.points, color)
        background = Object(*obj.loc, color, generator=generator)
        background.traits["decomp"] = "Base"
        background.traits["finished"] = True
        front = Object.from_points(front_points)
        candidate = Object(*obj.anchor, children=[background, front])
        candidate.traits["decomp"] = f"MB{color}"
        candidate.traits["finished"] = True
        candidate = self.repair(obj, candidate)
        if candidate:
            self.success(candidate)
        return candidate


class ConnectObjects(Process):
    def run(self, obj: Object) -> Object | None:
        self.info(obj)
        marked = obj.grid.copy()

        # TODO: we'll want to include context here soon
        off_colors = [cst.NULL_COLOR]

        for color in off_colors:
            marked[marked == color] = cst.MARKED_COLOR
        obj_pts, fail_message = color_connect(marked)
        if fail_message:
            self.fail(fail_message)
            return None
        children = []
        for idx, pts in enumerate(obj_pts):
            name = f"Conn{idx}"
            children.append(Object.from_points(pts, name=name))
        candidate = Object(*obj.loc, children=children)
        candidate.traits["decomp"] = "CO"
        candidate.traits["finished"] = True
        self.success(candidate)
        return candidate


class Tiling(Process):
    """Determine an optimal tiling of the object.

    First, determine the most probable size for a unit cell (R, C).
    Then, loop through each point in the unit cell and determine the color
    by majority vote.
    """

    def run(self, obj: Object) -> Object | None:
        self.info(obj)
        R, C, _ = obj.order
        # TODO: Consider whether the 1x1 order situation can replace
        # using MakeBase for rect-decomp
        if R == 1 and C == 1:
            return None
        # Check for a uniaxial tiling, indicated by a "1" for one of the axes
        elif R == 1:
            # NOTE this just needs to check R to switch the default axis, as above
            R = obj.grid.shape[0]
        elif C == 1:
            C = obj.grid.shape[1]

        # Identify each point that's part of the unit cell
        cell_pts: list[Point] = []
        noise = np.zeros(cst.N_COLORS)
        for i in range(R):
            for j in range(C):
                # Count how many times each color shows up in the sub-mesh
                active_mesh = obj.grid[i::R, j::C]
                cts = np.zeros(cst.N_COLORS)
                for row in active_mesh:
                    cts += np.bincount(row, minlength=cst.N_COLORS)
                # Eliminate colors from consideration based on context
                # if task and hasattr(task.context, "noise_colors"):
                #     for noise_color in task.context.noise_colors:
                #         cts[noise_color] = 0
                color = int(np.argmax(cts))
                cts[color] = 0
                noise += cts
                cell_pts.append((i, j, color))
        r_ct = np.ceil(obj.shape[0] / R)
        c_ct = np.ceil(obj.shape[1] / C)
        bound = None
        if obj.shape[0] % R or obj.shape[1] % C:
            bound = obj.shape
        log.debug(f"Tiling with {R}x{C} cell, bound: {bound}")
        gen = Generator.from_codes([f"R{r_ct - 1}", f"C{c_ct - 1}"], bound=bound)
        cell = Object.from_points(cell_pts, name=f"TBlock({R},{C})")
        cell.traits["decomp"] = "Cell"
        # TODO For now, assume unit cells are not worth sub-analyzing
        cell.traits["finished"] = True
        candidate = Object(
            *obj.loc, generator=gen, children=[cell], name=f"Tiling({R},{C})"
        )
        candidate.traits["decomp"] = "Tile"
        candidate.traits["finished"] = True
        candidate = self.repair(obj, candidate)
        if candidate:
            self.success(candidate)
        return candidate
