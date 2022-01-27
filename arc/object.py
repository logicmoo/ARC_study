from collections import Counter
from functools import cached_property
import logging
from typing import Any, Callable, TypeAlias

import numpy as np

from arc.types import Point, PointDict, PointList, Position, PositionList
from arc.util import dictutil, logger
from arc.grid_methods import (
    norm_points,
    translational_order,
)
from arc.definitions import Constants as cst
from arc.generator import Generator

log = logger.fancy_logger("Object", level=30)


class Object:
    def __init__(
        self,
        row: int = 0,
        col: int = 0,
        color: int = cst.NULL_COLOR,
        children: list["Object"] = None,
        generator: Generator = None,
        name: str = "",
        traits: dict[str, str | bool] = None,
    ):
        self.row = row
        self.col = col
        self.color = color
        self.children = children or []
        self.generator = generator
        self.name = name

        # Used during selection process
        self.traits = traits or {}

    ## Constructors
    @classmethod
    def from_grid(
        cls, grid: np.ndarray, seed: Point = (0, 0, cst.NULL_COLOR), name: str = ""
    ) -> "Object":
        children = []
        M, N = grid.shape
        for i in range(M):
            for j in range(N):
                if grid[i, j] != cst.NULL_COLOR:
                    children.append(cls(i, j, grid[i, j]))
        return cls(*seed, children=children, name=name)

    @classmethod
    def from_points(
        cls, points: PointList, loc: Position = (0, 0), name: str = ""
    ) -> "Object":
        """Create an Object from a list of Points.

        This is used during Generator.spawn to efficiently generate the
        points belonging to resulting objects.
        """
        if len(points) == 1:
            return cls(*points[0], name=name)
        norm_loc, normed, mono = norm_points(points)
        loc = (loc[0] + norm_loc[0], loc[1] + norm_loc[1])
        if mono:
            children = [Object(*pt[:2]) for pt in normed]
            return cls(*loc, normed[0][2], children=children, name=name)
        else:
            children = [Object(*pt) for pt in normed]
            return cls(*loc, children=children, name=name)

    ## Core properties
    @property
    def loc(self) -> tuple[int, int]:
        """The *local* position of the Object."""
        return (self.row, self.col)

    @property
    def seed(self) -> tuple[int, int, int]:
        """The *local* position and color information of the Object."""
        return (self.row, self.col, self.color)

    # NOTE: Keep an eye on the caching here to make sure it behaves appropriately
    @cached_property
    def normalized(self) -> "Object":
        if not self.generator:
            return self
        kernel = Object(
            color=self.color,
            children=[obj.normalized for obj in self.children],
        )
        new_obj = Object(*self.seed, children=self.generator.materialize(kernel))
        return new_obj

    @cached_property
    def points(self) -> PointDict:
        """Dict of all internal points defined by the Object."""
        if self.category == "Dot":
            return {(0, 0): self.color}

        if self.generator:
            return self.normalized.points

        pts: PointDict = {}
        # NOTE The order of children determines layering, bottom first
        for child in self.children:
            for loc, val in child.points.items():
                new_loc = (child.row + loc[0], child.col + loc[1])
                if val == cst.NEGATIVE_COLOR:
                    pts.pop(new_loc, None)
                elif val != cst.NULL_COLOR:
                    pts[new_loc] = val
                else:
                    pts[new_loc] = self.color
        return pts

    @cached_property
    def locs(self) -> PositionList:
        """Contains list of coordinates relative to the object's seed location"""
        return list(self.points.keys())

    @cached_property
    def grid(self) -> np.ndarray:
        """2D grid of the object"""
        if self.category == "Dot":
            return np.array([[self.color]], dtype=int)
        _grid = np.full(self.shape, cst.NULL_COLOR, dtype=int)
        for pos, val in self.points.items():
            _grid[pos] = val
        return _grid

    @cached_property
    def size(self) -> int:
        return len(self.points)

    @cached_property
    def category(self) -> str:
        """A single-word description of the Object."""
        if self.color == cst.NEGATIVE_COLOR:
            return "Cutout"
        elif not self.children:
            if not self.generator:
                return "Dot"
            elif self.generator.dim == 1:
                return "Line"
            elif self.generator.dim == 2:
                return "Rect"
            else:
                return "Compound"
        else:
            if self.generator and self.generator.dim > 0:
                return "Tile"
            elif all([kid.category == "Dot" for kid in self.children]):
                return "Cluster"
            else:
                return "Container"

    @cached_property
    def shape(self) -> tuple[int, int]:
        """The bounding dimensions of the Object."""
        if self.category == "Dot":
            return (1, 1)
        maxrow = max([pos[0] for pos in self.points])
        maxcol = max([pos[1] for pos in self.points])
        return (maxrow + 1, maxcol + 1)

    # TODO Unused, eliminate?
    @cached_property
    def center(self):
        row = self.seed[0] + (self.shape[0] - 1) / 2
        col = self.seed[1] + (self.shape[1] - 1) / 2
        return (row, col)

    ## Comparisons
    def __eq__(self, other: "Object") -> bool:
        return self.loc == other.loc and self.points == other.points

    def sim(self, other: "Object") -> bool:
        """Tests if objects are same up to translation"""
        return self.points == other.points

    def sil(self, other: "Object") -> bool:
        """Tests if objects have the same 'outline', i.e. ignore color"""
        return self.locs == other.locs

    def __lt__(self, other: "Object") -> bool:
        """Compare Objects based on their size (total points), shape, and location.

        This primarily is used for providing operational determinism via sorting.
        """
        if self.size != other.size:
            return self.size < other.size
        elif self.shape != other.shape:
            return self.shape < other.shape
        elif self.seed != other.seed:
            return self.seed < other.seed
        else:
            return False

    def issubset(self, other: "Object") -> bool:
        return set(self.points).issubset(other.points)

    ## Utility Methods
    def __getitem__(self, key: int) -> "Object":
        return self.children[key]

    #! Properties relying on the traits dictionary shouldn't be cached
    @property
    def _id(self) -> str:
        """A concise, (nearly) unique description of the Object."""
        if self.category == "Dot":
            shape_str = ""
        else:
            shape_str = f"({self.shape[0]}x{self.shape[1]})"
        link = "*" if self.traits.get("decomp") == "Scene" else ""
        return f"{link}{self.category}{shape_str}@{self.seed}"

    def __repr__(self) -> str:
        """One line description of what the object is"""
        if self.category == "Dot":
            info = ""
        else:
            info = f"({len(self.children)}ch, {self.size}pts, {self.props}p)"
        decomp = f"[{self.traits.get('decomp', '')}]"
        return f"{decomp}{self._id}{info}"

    def _hier_repr(self, tab: int = 0, max_lines: int = 10, max_dots: int = 5) -> str:
        """Detailed info on object and its children"""
        indent = "  " * tab
        output = [indent + self.__repr__()]
        dot_kids = 0
        for child in self.children:
            if child.category == "Dot":
                dot_kids += 1
            if dot_kids < max_dots:
                output.append(f"{child._hier_repr(tab=tab+1)}")
        if dot_kids >= max_dots:
            output.append(f"{indent}  ...{dot_kids} Dots total")

        if self.generator:
            output.append(f"{indent}  Gen{self.generator}")
        # Limit output to 'max_lines' by truncating remainder
        if len(output) > max_lines and "..." not in output:
            output = output[:max_lines] + ["..."]
        return "\n".join(output)

    @cached_property
    def history(self) -> list[str]:
        hist = [str(self.traits.get("decomp")) or ""]
        for kid in self.children:
            hist.extend(kid.history)
        return hist

    # TODO Redo printing of information to be more coherent with other methods
    def info(self, level: logger.LogLevel = "info", max_lines: int = 10) -> None:
        """Log the Object's hierarchy, with full header info."""
        # Quit early if we can't print the output
        if log.level > getattr(logging, level.upper()):
            return
        for line in self._hier_repr().split("\n"):
            getattr(log, level)(line)

    def spawn(self, seed: tuple[int, int, int] = None, **kwargs) -> "Object":
        seed = seed or self.seed
        if self.category == "Dot":
            return Object(*seed)
        # Perhaps altering children isn't necessary in most cases
        new_args = {
            "children": [kid.spawn() for kid in self.children],
            "generator": self.generator,
            "traits": None if self.traits is None else self.traits.copy(),
        }
        new_args.update(kwargs)
        return Object(*seed, **new_args)

    def flatten(self) -> "Object":
        """Eliminate unnecessary hierchical levels in Object representation.

        Recursively move through the representation and identify any Objects
        that could be "up-leveled". An example of upleveling would be when a
        series of "connect on common color" operations yield 3+ clusters of
        points. These might start on different levels of the hierarchy, but
        could be all placed on the same level.
        """
        # NOTE: We may also want to flatten objects with generators and non-dot
        # children; perhaps it isn't too complicated.

        # Containers have no generators, and have some non-Dot children
        if self.category != "Container":
            return self
        new_children = []
        for kid in self.children:
            flat_kid = kid.flatten()
            # We can't currently flatten containers with cutouts. Food for thought?
            if any([gkid.category == "Cutout" for gkid in flat_kid.children]):
                new_children.append(flat_kid)
                continue

            if len(flat_kid.children) == 1 or (
                flat_kid.category == "Container" and flat_kid.color == cst.NULL_COLOR
            ):
                log.debug(f"Flattening {flat_kid}")
                uplevel = []
                for gkid in flat_kid.children:
                    row, col = gkid.row + kid.row, gkid.col + kid.col
                    uplevel.append(gkid.spawn(seed=(row, col, gkid.color)))
                new_children.extend(uplevel)
            else:
                new_children.append(flat_kid)
        return self.spawn(self.seed, children=new_children)

    def overlap(self, other: "Object") -> tuple[float, float]:
        ct = np.sum(self.grid == other.grid)
        return ct / self.grid.size, ct

    @cached_property
    def props(self) -> int:
        """Count how many properties are used in this Object representation.

        This is a core piece of information used to determine the "value" of
        a representation--the more compact the better. There is some leeway
        in this definition, which might be a central point of consideration
        for achieving success in applications.
        """
        # When we have a contextual reference, we already "know" the object
        if self.traits.get("decomp") == "scene":
            return 1

        # Calculate local information used (self existence, positions, and color)
        from_pos = int(self.row != 0) + int(self.col != 0)
        own_props = from_pos + int(self.color != cst.NULL_COLOR)

        if self.category == "Dot":
            return cst.DOT_PROPS + own_props

        from_children = sum([item.props for item in self.children])
        from_gen = 0 if not self.generator else self.generator.props
        return cst.NON_DOT_PROPS + own_props + from_gen + from_children

    @cached_property
    def c_rank(self) -> list[tuple[int, int]]:
        """Get the counts for each color on the grid, starting with most prevalent"""
        counter = Counter(self.points.values())
        return sorted(counter.items(), key=lambda x: x[1], reverse=True)

    @cached_property
    def order(self) -> tuple[int, int, float]:
        if self.category == "Dot":
            return (1, 1, 1)
        # Get the most-ordered stride for each axis
        row_o = translational_order(self.grid, row_axis=True)[0]
        col_o = translational_order(self.grid, row_axis=False)[0]
        # TODO The product of individual dimension order fraction is almost certainly wrong...
        # Also, the "default" order should be the full size of the dimension, not 1
        return (row_o[0], col_o[0], row_o[1] * col_o[1])

    # TODO: WIP
    def inventory(self, leaf_only=False, depth=0, max_dots=10):
        if self.category == "Dot":
            return [self]
        elif self.category == "Cluster":
            # If we have a cluster, only accept child dots if there aren't many
            if len(self.children) <= max_dots:
                return [self] + self.children
            else:
                return [self]
        res = [self]
        if leaf_only and self.children:
            res = []
        for kid in self.children:
            add = kid.inventory(leaf_only=leaf_only, depth=depth + 1, max_dots=max_dots)
            res.extend(add)
        return res


ObjectComparison: TypeAlias = Callable[[Object, Object], tuple[int, dict[str, Any]]]


class ObjectDelta:
    """Determine the 'difference' between two objects.

    This class analyzes how many transformations and properties it requires to
    turn the 'left' object into the 'right'. It calculates an integer measure called
    'distance', as well as the series of standard transformations to apply.
    """

    def __init__(self, obj1: Object, obj2: Object, comparisons: list[ObjectComparison]):
        self.dist = 0
        self.left = obj1
        self.right = obj2
        self.transform = {}
        self.comparisons = comparisons
        if obj1 == obj2:
            return

        for comparison in comparisons:
            dist, trans = comparison(self.left, self.right)
            self.dist += dist
            self.transform.update(trans)

    @property
    def _name(self):
        header = f"Delta({self.dist}): "
        trans = ""
        for item in self.transform:
            trans += f"{item}"
        return header + f"[{trans}]"

    def __repr__(self) -> str:
        return f"{self._name}: {self.right._id} -> {self.left._id}"

    def __lt__(self, other: "ObjectDelta") -> bool:
        return self.dist < other.dist

    # TODO Does this make sense?
    def __sub__(self, other):
        """Returns a distance between transforms, used for selection grouping"""
        # First is the distance between base objects (uses ObjectDelta)
        dist = ObjectDelta(self.right, other.right, self.comparisons).dist

        # Then, add in the difference in transforms
        d_xor = dictutil.dict_xor(self.transform, other.transform)
        dist += len(d_xor)
        return dist
