from typing import Any
import numpy as np
from arc.contexts import Context
from abc import ABC, abstractmethod
from arc.generator import Generator

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

    def patch(self, input: Object, output: Object) -> Object | None:
        """Repair any inconsistencies between input and output."""
        if input == output:
            return output
        # TODO: For now, assume we can't fix missing points
        missing_locs = input.points.keys() - output.points.keys()
        if missing_locs:
            log.debug("  Extra points during patch")
            return None

        extra_locs = output.points.keys() - input.points.keys()
        cut_points = [(*loc, cst.NEGATIVE_COLOR) for loc in extra_locs]
        log.debug(f"  Cutting {len(cut_points)} points as patch")
        loc = output.loc
        out = output.spawn(seed=(0, 0, output.color))
        cutout = Object.from_points(cut_points)
        cutout.traits["decomp"] = "Cut"
        # TODO: For now, assume we only patch up near a complete representation
        cutout.traits["finished"] = True
        cut_container = Object(*loc, children=[out, cutout])
        cut_container.traits["decomp"] = output.traits["decomp"]
        cut_container.traits["finished"] = output.traits["finished"]
        return cut_container

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
        result = Object(*obj.loc, children=[match, other])
        result.traits["decomp"] = f"SC{color}"
        result.traits["finished"] = True
        self.success(result)
        return result


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
            result = Object(*obj.loc, color, generator=generator)
            result.traits["decomp"] = f"MB{color}"
            result.traits["finished"] = True
            result = self.patch(obj, result)
            if result:
                self.success(result, "single color")
            return result

        # Split off the base color from the "front matter"
        _, front_points = point_filter(obj.points, color)
        background = Object(*obj.loc, color, generator=generator)
        background.traits["decomp"] = "Base"
        background.traits["finished"] = True
        front = Object.from_points(front_points)
        result = Object(*obj.seed, children=[background, front])
        result.traits["decomp"] = f"MB{color}"
        result.traits["finished"] = True
        result = self.patch(obj, result)
        if result:
            self.success(result)
        return result


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
        result = Object(*obj.loc, children=children)
        result.traits["decomp"] = "CO"
        result.traits["finished"] = True
        self.success(result)
        return result


class Tiling(Process):
    def run(self, obj: Object) -> dict[str, Any] | None:
        R, C, _ = obj.order
        # If there's no tiling order, try making a base layer
        if R == 1 and C == 1:
            return None
        # Check for a uniaxial tiling, indicated by a "1" for one of the axes
        elif R == 1:
            # NOTE this just needs to check R to switch the default axis, as above
            R = obj.grid.shape[0]
        elif C == 1:
            C = obj.grid.shape[1]

        # Track the points in the repeated block, also which colors cause noise
        tile_pts, noise = [], np.zeros(cst.N_COLORS)
        # For each i,j in the repeated block, figure out the most likely color
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
                color = np.argmax(cts)
                cts[color] = 0
                noise += cts
                tile_pts.append((i, j, color))
        r_ct = np.ceil(obj.shape[0] / R)
        c_ct = np.ceil(obj.shape[1] / C)
        bound = None
        if obj.shape[0] % R or obj.shape[1] % C:
            bound = obj.shape
        args = dict(
            gens=[f"R{r_ct - 1}", f"C{c_ct - 1}"],
            children=[dict(pts=tile_pts, name=f"TBlock({R},{C})")],
            bound=bound,
            name=f"Tiling({R},{C})",
            decomposed="Tile",
        )
        # if task:
        #     task.context.noise += noise
        return args
