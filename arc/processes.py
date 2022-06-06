from abc import ABC, abstractmethod
import collections

import numpy as np

from arc.generator import Generator
from arc.types import Point, PointList, PositionSet
from arc.util import logger
from arc.grid_methods import eval_mesh, point_filter
from arc.definitions import Constants as cst
from arc.object import Object
from arc.util.common import process_exception

log = logger.fancy_logger("Processes", level=30)


class Process(ABC):
    code: str = ""

    def __init__(self):
        pass

    def test(self, object: Object) -> bool:
        """Check whether we believe we should run this process."""
        return True

    def cell_test(self, object: Object, min_size: int, min_dim: int) -> bool:
        """Common test for repeated elements (tiles, rotation, flip)."""
        # A cell should have at least 4 points for symmetry to be useful
        if object.size < min_size:
            return False
        # A cell should have a dimension of at least 3 in one direction
        elif object.shape[0] < min_dim and object.shape[1] < min_dim:
            return False
        return True

    def repair(
        self, input: Object, output: Object, occlusion: PositionSet
    ) -> Object | None:
        """Repair any inconsistencies between input and output."""
        if input == output:
            return output
        elif len(output.points) == 0:
            log.warning(f"Process {self.__class__.__name__} generated empty object")
            return None

        log.debug(f"Patching {output} -> {input}")
        if missing_locs := input.points.keys() - output.points.keys():
            # TODO: For now, assume we can't fix missing points
            log.debug("  Missing output points during patch")
            log.debug(missing_locs)
            return None
        elif extra_locs := output.points.keys() - input.points.keys() - occlusion:
            # TODO Don't use cutouts for now
            log.debug(f"  (not implemented) {len(extra_locs)} extra points")
            return None
            # cut_points = [(*loc, cst.NEGATIVE_COLOR) for loc in extra_locs]
            # log.debug(f"  Cutting {len(cut_points)} points as patch")
            # return self.add_patch(output, cut_points, "Cut")
        else:
            # At this point, the silhouetes match, so there is just color
            # disagreement from the input and output.
            recolor_pts: PointList = []
            for loc, color in input.points.items():
                if output.points[loc] != color:
                    recolor_pts.append((*loc, color))

            # If the disagreement is occluded, we will end up with no recolor_pts.
            if not recolor_pts:
                return output

            log.debug(f"  Recoloring {len(recolor_pts)} points as patch")
            return self.add_patch(output, recolor_pts, "Reco")

    def add_patch(self, output: Object, points: PointList, tag: str) -> Object:
        """Create a container that will contain the Process output and patch."""
        out = output.copy(anchor=(0, 0, output.color))
        patch = Object.from_points(points, leaf=True, process=tag)
        # NOTE: The use of output.anchor vs output.loc is contentious
        kwargs = {"leaf": output.leaf, "process": output.process}
        container = Object(*output.anchor, children=[out, patch], **kwargs)
        return container

    def run(self, object: Object, occlusion: PositionSet = set([])) -> Object | None:
        self.info(object)
        try:
            if candidate := self.apply(object):
                if repaired := self.repair(object, candidate, occlusion):
                    self.success(candidate)
                    return repaired
                else:
                    self.fail("Repair unsuccessful")
                    return None
            else:
                return None
        except Exception as _:
            exception = process_exception()
            log.error(f"{exception[0]} exception during {self.__class__.__name__}")
            log.error(logger.pretty_traceback(*exception))
            return None

    @abstractmethod
    def apply(self, object: Object) -> Object | None:
        pass

    def info(self, object: Object) -> None:
        log.debug(f"Running {self.__class__.__name__} on {object.id}")

    def fail(self, message: str) -> None:
        log.debug(f"  ...failed: {message}")

    def success(self, object: Object, message: str = "") -> None:
        msg_str = f"({message})" if message else ""
        log.debug(f"  ...finished: {(object.props)} props {msg_str}")


class Processes:
    map: dict[str, type[Process]] = {}

    class SeparateColor(Process):
        def test(self, object: Object) -> bool:
            return len(object.c_rank) > 1

        def apply(self, object: Object) -> Object | None:
            """Improves representation by putting all points of one color together."""
            color = object.c_rank[0][0]

            match_pts, other_pts = point_filter(object.points, color)
            match = Object.from_points(match_pts)
            other = Object.from_points(other_pts)
            candidate = Object(
                *object.loc,
                children=[match, other],
                leaf=True,
                process=f"{self.code}{color}",
            )
            return candidate

    class Background(Process):
        def apply(self, object: Object) -> Object | None:
            # NOTE: This currently assumes a black background if black is present
            # which should be altered later to be more data-driven.
            if 0 in [item[0] for item in object.c_rank]:
                color = 0
            # Select a color to use, based on area covered by the color
            else:
                color = object.c_rank[0][0]

            # Create a Generator based on the grid size
            codes: tuple[str, ...] = tuple([])
            rows, cols = object.grid.shape
            if cols > 1:
                codes += (f"H*{cols - 1}",)
            if rows > 1:
                codes += (f"V*{rows - 1}",)
            generator = Generator.from_codes(codes) if codes else None

            # For a single color present, this simplifies to a single line/rect
            if len(object.c_rank) == 1:
                return Object(
                    *object.loc,
                    color=color,
                    generator=generator,
                    leaf=True,
                    process=f"{self.code}{color}",
                )

            # Split off the base color from the "front matter"
            _, front_points = point_filter(object.points, color)
            background = Object(
                color=color, generator=generator, leaf=True, process="BG"
            )
            front = Object.from_points(front_points, process="Btop")
            return Object(
                *object.loc,
                children=[background, front],
                leaf=True,
                process=f"{self.code}{color}",
            )

    class ConnectObjects(Process):
        """Cluster points together that aren't of masked colors."""

        def test(self, object: Object) -> bool:
            return 1 < object.connectedness < cst.MAX_BLOBS

        def apply(self, object: Object) -> Object | None:
            object_pts = object.blobs
            children: list[Object] = []
            for idx, pts in enumerate(object_pts):
                name = f"Conn{idx}"
                children.append(Object.from_points(pts, name=name, process="Conn"))
            return Object(*object.loc, children=children, leaf=True, process="Conn")

    class Tiling(Process):
        """Determine an optimal tiling of the object.

        First, determine the most probable size for a unit cell (R, C).
        Then, loop through each point in the unit cell and determine the color
        by majority vote.
        """

        threshold = 0.9

        def test(self, object: Object) -> bool:
            if not self.cell_test(object, 4, 3):
                return False
            R, row_level = object.order_trans_row
            C, col_level = object.order_trans_col
            if (R, C) == object.shape:
                return False
            if row_level < self.threshold and col_level < self.threshold:
                return False
            return True

        def apply(self, object: Object) -> Object | None:
            row_stride, row_level = object.order_trans_row
            col_stride, col_level = object.order_trans_col

            if row_level < self.threshold:
                row_stride = object.shape[0]
            if col_level < self.threshold:
                col_stride = object.shape[1]

            # Identify each point that's part of the unit cell
            cell_pts = eval_mesh(object.grid, row_stride, col_stride)
            if not cell_pts:
                log.debug(f"Empty cell pts generated from following object")
                object.debug()
                return None

            r_ct = np.ceil(object.shape[0] / row_stride)
            c_ct = np.ceil(object.shape[1] / col_stride)
            row_bound, col_bound = (cst.MAX_ROWS, cst.MAX_COLS)
            if object.shape[0] % row_stride or object.shape[1] % col_stride:
                row_bound, col_bound = object.shape
            log.debug(
                f"Tiling with {row_stride}x{col_stride} cell, bound: {row_bound, col_bound}"
            )
            codes: tuple[str, ...] = tuple([])
            if r_ct > 1:
                codes += (f"V*{r_ct-1}",)
            if c_ct > 1:
                codes += (f"H*{c_ct-1}",)
            gen = Generator.from_codes(codes)
            log.debug(f"Generator: {gen}")
            # TODO For now, assume unit cells are not worth sub-analyzing
            cell = Object.from_points(
                cell_pts,
                leaf=True,
                process="Cell",
            )
            return Object(
                *object.loc,
                generator=gen,
                children=[cell],
                row_bound=row_bound,
                col_bound=col_bound,
                leaf=True,
                process="Tile",
            )

    class Reflection(Process):
        """Determine any mirror symmetries."""

        threshold = 0.9

        def test(self, object: Object) -> bool:
            if not self.cell_test(object, 4, 3):
                return False
            r_level, c_level = object.order_mirror
            if r_level < self.threshold and c_level < self.threshold:
                return False
            return True

        def apply(self, object: Object) -> Object | None:
            axes = [False, False]
            R, C = object.shape
            rs, cs = R, C
            odd_vertical = R % 2 == 1
            odd_horizontal = C % 2 == 1
            if object.order_mirror[0] >= self.threshold:
                rs = R // 2 + int(odd_vertical)
                axes[0] = True
            if object.order_mirror[1] >= self.threshold:
                cs = C // 2 + int(odd_horizontal)
                axes[1] = True

            # grid_v = np.flip(obj.grid, 0)
            # grid_h = np.flip(obj.grid, 1)
            # Identify each point that's part of the unit cell
            cell_pts: list[Point] = []
            for i in range(rs):
                for j in range(cs):
                    base_color = object.grid[i, j]

                    # TODO will need to handle noise similar to Tiling
                    # if base_color != ref_color:
                    # pass
                    if base_color != cst.NULL_COLOR:
                        cell_pts.append((i, j, base_color))

            if not cell_pts:
                log.debug(f"Empty cell pts generated from following object")
                object.debug()
                return None
            codes: tuple[str, ...] = tuple([])
            if axes[0]:
                if odd_vertical:
                    codes += ("m*1",)
                else:
                    codes += ("M*1",)
            if axes[1]:
                if odd_horizontal:
                    codes += ("e*1",)
                else:
                    codes += ("E*1",)
            gen = Generator.from_codes(codes)
            # TODO Should we assume unit cells are not worth sub-analyzing?
            # e.g. should we set leaf=True in the args below
            cell = Object.from_points(cell_pts, leaf=True, process="Cell")
            candidate = Object(
                *object.loc,
                color=cell.color,
                generator=gen,
                children=[cell],
                leaf=True,
                process="Refl",
            )
            return candidate

    class Rotation(Process):
        """Determine any mirror symmetries."""

        threshold = 0.8

        def test(self, object: Object) -> bool:
            if not self.cell_test(object, 4, 3):
                return False

            # TODO Handle 180 deg rotations, which can have mismatched shape params
            elif object.shape[0] != object.shape[1]:
                return False
            # Odd shaped rot symmetry is equivalent to mirror symmetry
            elif object.shape[0] % 2 == 1:
                return False
            elif object.order_rotation[1] < self.threshold:
                return False
            return True

        def apply(self, object: Object) -> Object | None:
            # TODO WIP How many cases of combining rotated elements are there?
            # Case 1: Commensurate 90 (no overlap), even shape values
            R, C = object.shape
            rs, cs = R // 2, C // 2

            cell_pts: list[Point] = []
            for i in range(rs):
                for j in range(cs):
                    # Sub-mask for 90 deg rotation
                    locs = [
                        (i, j),
                        (R - 1 - j, i),
                        (j, C - 1 - j),
                        (R - 1 - i, C - 1 - j),
                    ]
                    colors = [object.grid[r, c] for r, c in locs]
                    base_color = collections.Counter(colors).most_common()[0][0]

                    # TODO will need to handle noise similar to Tiling
                    # if base_color != ref_color:
                    # pass
                    if base_color != cst.NULL_COLOR:
                        cell_pts.append((i, j, base_color))

            if not cell_pts:
                log.debug(f"Empty cell pts generated from following object")
                object.debug()
                return None

            codes: tuple[str, ...] = tuple([])
            codes += ("O*3",)
            gen = Generator.from_codes(codes)
            # TODO For now, assume unit cells are not worth sub-analyzing
            cell = Object.from_points(cell_pts, leaf=True, process="Cell")
            candidate = Object(
                *object.loc, generator=gen, children=[cell], leaf=True, process="Rot"
            )
            return candidate


process_map: dict[str, type[Process]] = {
    "B": Processes.Background,
    "C": Processes.ConnectObjects,
    "S": Processes.SeparateColor,
    "T": Processes.Tiling,
    "R": Processes.Reflection,
    "O": Processes.Rotation,
}

for code, process in process_map.items():
    process.code = code
    Processes.map[code] = process
