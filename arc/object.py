from functools import cached_property
from typing import Any, Callable, TypeAlias

import numpy as np
from arc.types import PointDict, PositionList

from arc.util import dictutil, logger
from arc.grid_methods import (
    PointList,
    norm_pts,
    norm_children,
    translational_order,
)
from arc.concepts import Gen
from arc.definitions import Constants as cst

log = logger.fancy_logger("Object", level=30)


class Object:
    def __init__(
        self,
        row: int = 0,
        col: int = 0,
        color: int = cst.NULL_COLOR,
        parent: "Object" = None,
        bound: tuple[int, int] = None,
        name: str = "",
        decomposed: str = "",
        gens: list[str] = None,
        children: list["Object"] = None,
    ):
        self.row = row
        self.col = col
        self.color = color
        self.parent = parent
        self.bound = bound
        self.gens = gens or []
        self.children = children or []
        self.name = name

        # Used during decomposition process
        self.decomposed = decomposed
        self.occ = set([])

        # Used during selection process
        self.traits = {}

        # Internal variables for properties
        self._props = None
        self._c_rank = None
        self._order = None

        # Special initializations based on inputs
        if children:
            self.adopt()

    @classmethod
    def from_grid(cls, grid: np.ndarray, name: str = "") -> "Object":
        new_object = cls(name=name)
        children = []
        M, N = grid.shape
        for i in range(M):
            for j in range(N):
                children.append(cls(i, j, grid[i, j], parent=new_object))
        return new_object

    @classmethod
    def from_points(cls, points: PointList, name: str = "") -> "Object":
        if len(points) == 1:
            return cls(*points[0], name=name)
        seed, normed = norm_pts(points)
        new_object = cls(*seed)
        children = [Object(*pt, parent=new_object) for pt in normed]
        new_object.children = children
        return new_object

    @property
    def seed(self) -> tuple[int, int, int]:
        """The *local* position and color information of the Object."""
        return (self.row, self.col, self.color)

    @cached_property
    def anchor(self) -> tuple[int, int, int]:
        """The *global* position and color information of the Object."""
        if self.parent is None:
            return self.seed
        return (
            self.row + self.parent.anchor[0],
            self.col + self.parent.anchor[1],
            self.color if self.color != cst.NULL_COLOR else self.parent.color,
        )

    @cached_property
    def category(self) -> str:
        """A single-word description of the Object."""
        if not self.children:
            if not self.gens:
                return "Dot"
            elif len(self.gens) == 1:
                return "Line"
            elif len(self.gens) == 2:
                return "Rect"
            else:
                return "Compound"
        else:
            if len(self.gens) > 0:
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
        maxrow = max([pos[0] for pos in self.pts])
        maxcol = max([pos[1] for pos in self.pts])
        return (maxrow + 1, maxcol + 1)

    @property
    def center(self):
        # TODO Unused, eliminate?
        row = self.seed[0] + (self.shape[0] - 1) / 2
        col = self.seed[1] + (self.shape[1] - 1) / 2
        return (row, col)

    @property
    def size(self) -> int:
        return len(self.pts)

    @property
    def _id(self) -> str:
        """A concise, (nearly) unique description of the Object."""
        if self.category == "Dot":
            shape_name = ""
        else:
            shape_name = f"({self.shape[0]}x{self.shape[1]})"
        link = "*" if self.decomposed == "Scene" else ""
        return f"{link}{self.category}{shape_name}@{self.anchor}"

    def __repr__(self) -> str:
        """One line description of what the object is"""
        if self.category == "Dot":
            info = ""
        else:
            info = f"({len(self.children)}ch, {self.size}pts, {self.props}p)"
        header = f"{self._id}{info}"
        return header

    def info(self, tab=0, cond=10) -> str:
        """Detailed info on object and its children"""
        ind = "  " * tab
        output = [ind + self.__repr__()]
        for idx, child in enumerate(self.children):
            output.append(f"{child.info(tab=tab+1)}")
        if self.gens:
            output.append(f"{ind}  Gen{self.gens}")
        # Condense output to just cond lines
        if len(output) > cond and "..." not in output:
            output = output[:cond] + ["..."]
        return "\n".join(output)

    # TODO Redo printing of information to be more coherent with other methods
    def ppt(self, level="info") -> None:
        for line in self.info().split("\n"):
            getattr(log, level)(line)

    def __eq__(self, other: "Object") -> bool:
        return self.pts == other.pts

    def __lt__(self, other: "Object") -> bool:
        """Compare Objects based on their size (total points), shape, and location.

        This primarily is used for providing operational determinism via sorting.
        """
        if self.size != other.size:
            return self.size < other.size
        elif self.shape != other.shape:
            return self.shape < other.shape
        elif self.anchor != other.anchor:
            return self.anchor < other.anchor
        else:
            return False

    def __getitem__(self, key: int) -> "Object":
        return self.children[key]

    def spawn(self, *args, **kwargs) -> "Object":
        if self.category == "Dot":
            # A dot will never have kwargs
            return Object(*(args + self.seed[len(args) :]))
        base_args = ["row", "col", "color", "parent", "bound", "name", "decomposed"]
        new_args = {arg: getattr(self, arg) for arg in base_args}
        for key, val in zip(base_args, args):
            new_args[key] = val
        if self.gens and "gens" not in kwargs:
            new_args["gens"] = self.gens.copy()
        if self.children and "children" not in kwargs:
            new_args["children"] = [kid.spawn() for kid in self.children]
        new_args.update(kwargs)
        new_obj = Object(**new_args)

        # Tracking variables that need to be carried over
        new_obj.occ = self.occ.copy()
        return new_obj

    def reset(self):
        self._grid = None
        self._pts = None
        self._pos = None
        self._shape = None
        self._props = None
        self._c_rank = None
        self._order = None
        for child in self.children:
            child.reset()

    # TODO Redo in top-down fashion, at Board-level
    @property
    def history(self):
        result = [self.decomposed] if self.decomposed else []
        if self.parent:
            result = self.parent.history + result
        return result

    def adopt(self):
        """Ensures parental connection, normed seed, and attributes are reset"""
        minrow, mincol = norm_children(self.children)
        if minrow or mincol:
            log.debug(f"Kid norming: {self.name}")
            self.row += minrow
            self.col += mincol
        for child in self.children:
            child.parent = self
        self.reset()

    def flatten(self) -> list["Object"]:
        """Eliminate unnecessary hierchical levels in Object representation.

        Recursively move through the representation and identify any Objects
        that could be "up-leveled". An example of upleveling would be when a
        series of "connect on common color" operations yield 3+ clusters of
        points. These might start on different levels of the hierarchy, but
        could be all placed on the same level.
        """
        # Containers have no generators, and have some non-Dot children
        if self.category != "Container":
            return [self]
        new_children = []
        for kid in self.children:
            new_children.extend(kid.flatten())
        if self.parent and self.color == cst.NULL_COLOR:
            log.debug(f"Flattening {self}")
            uplevel = []
            for kid in new_children:
                row, col = kid.row + self.row, kid.col + self.col
                uplevel.append(kid.spawn(row=row, col=col))
            return uplevel
        else:
            return [self.spawn(children=new_children)]

    def adult(self):
        """Removes parent and sets seed to anchor"""
        self.row, self.col, self.color = self.anchor
        self.parent = None

    def issubset(self, other: "Object") -> bool:
        return set(self.pts).issubset(other.pts)

    def sim(self, other: "Object") -> bool:
        """Tests if objects are same up to translation"""
        if not self.shape == other.shape:
            return False
        return (self.grid == other.grid).all()

    def sil(self, other: "Object") -> bool:
        """Tests if objects have the same 'outline', i.e. ignore color"""
        if not self.shape == other.shape:
            return False
        return self.pos == other.pos

    def overlap(self, other: "Object") -> tuple[float, float]:
        ct = np.sum(self.grid == other.grid)
        return ct / self.grid.size, ct

    @cached_property
    def grid(self):
        """2D grid, inheriting color but not position"""
        if self.category == "Dot":
            return np.array([[self.anchor[2]]], dtype=int)
        _grid = np.full(self.shape, cst.NULL_COLOR, dtype=int)
        for pos, val in self.pts.items():
            _grid[pos] = val
        return _grid

    @cached_property
    def pts(self) -> PointDict:
        """Dict of all points defined by the Object."""
        if self.category == "Dot":
            return {(0, 0): self.anchor[2]}

        # Generators are applied to either the implied object (Dot at self coords)
        # Or else we apply the gens to each child
        layers = self.children or [Object(0, 0, self.color)]
        # TODO gen refactor
        for gen in self.gens:
            spawned = []
            for obj in layers:
                spawned.extend(Gen(gen).create(obj))
            layers = spawned
        # This gets all pts from children and layers them in order
        # Only retrieve points within the defined bound
        _pts: PointDict = {}
        max_row, max_col = self.bound or (cst.MAX_ROWS, cst.MAX_COLS)
        for obj in layers:
            if obj.category == "Dot":
                _pts[obj.anchor[:2]] = obj.anchor[2]
                continue
            for pos, val in obj.pts.items():
                row = pos[0] + obj.row
                col = pos[1] + obj.col
                if row < max_row and col < max_col:
                    _pts[(row, col)] = val
        return _pts

    @cached_property
    def pos(self) -> PositionList:
        """Contains list of coordinates relative to the object anchor point"""
        return list(self.pts.keys())

    @property
    def props(self) -> int:
        """Count how many properties are used in this Object representation.

        This is a core piece of information used to determine the "value" of
        a representation--the more compact the better. There is some leeway
        in this definition, which might be a central point of consideration
        for achieving success in applications.
        """
        if self._props is not None:
            return self._props
        # When we have a contextual reference, we already "know" the object
        if self.decomposed == "Scene":
            self._props = 1
            return self._props

        # Calculate local information used (self existence, positions, and color)
        from_pos = int(self.row != 0) + int(self.col != 0)
        own_props = from_pos + int(self.color != cst.NULL_COLOR)
        self._props = 1 + own_props

        if self.category == "Dot":
            return self._props

        # Add up total actions on gens?
        # TODO Gen refactor
        of_gens = sum([len(str(gen)) for gen in self.gens])
        of_children = sum([item.props for item in self.children])
        # Include a constant amount for being something non-Dot
        self._props += 1 + of_gens + of_children
        return self._props

    @property
    def c_rank(self) -> list[tuple[int, int]]:
        """Get the counts for each color on the grid, starting with most prevalent"""
        if self._c_rank is not None:
            return self._c_rank
        # np.unique is an indeterminate type due to "return_counts"
        cts: list[tuple[int, int]] = list(zip(*np.unique(self.grid, return_counts=True)))  # type: ignore
        sorted_cts = sorted(cts, key=lambda x: x[1], reverse=True)
        self._c_rank = [
            (color, ct) for color, ct in sorted_cts if color != cst.NULL_COLOR
        ]
        return self._c_rank

    @property
    def order(self) -> tuple[int, int, float]:
        if self._order is not None:
            return self._order
        if self.category == "Dot":
            self._order = (1, 1, 1)
            return self._order
        # Get the most-ordered stride for each axis
        row_o = translational_order(self.grid, row_axis=True)[0]
        col_o = translational_order(self.grid, row_axis=False)[0]
        # TODO The product of individual dimension order fraction is almost certainly wrong...
        # Also, the "default" order should be the full size of the dimension, not 1
        self._order = (row_o[0], col_o[0], row_o[1] * col_o[1])
        return self._order

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
