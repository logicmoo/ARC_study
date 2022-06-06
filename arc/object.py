import collections
from functools import cached_property
from typing import Any
import uuid

from arc.types import (
    BaseObjectPath,
    BoardData,
    Grid,
    Point,
    PointDict,
    PointList,
    Position,
    PositionList,
    PropertyPath,
)
from arc.util import logger
from arc.grid_methods import (
    connect,
    get_boundary,
    grid_overlap,
    gridify,
    mirror_order,
    norm_points,
    rotational_order,
    translational_order,
)
from arc.definitions import Constants as cst
from arc.generator import Generator

log = logger.fancy_logger("Object", level=30)


class EmptyObject(Exception):
    pass


class ObjectPath:
    """Accessor for any parameter of an Object."""

    def __init__(
        self, base: BaseObjectPath = tuple([]), property: PropertyPath | None = None
    ) -> None:
        self.base = base
        self.property = property

    def __eq__(self, other: "ObjectPath") -> bool:
        return self.base == other.base and self.property == other.property

    def __lt__(self, other: "ObjectPath") -> bool:
        if self.base < other.base:
            return True
        elif self.base > other.base:
            return False
        else:
            return str(self.property) < str(other.property)

    def __bool__(self) -> bool:
        if self.base == tuple([]) and self.property is None:
            return False
        else:
            return True

    def __hash__(self) -> int:
        return hash(self.__repr__())

    def __iter__(self):
        return self.base.__iter__()

    def __repr__(self) -> str:
        prop_str = f".{self.property}" if self.property else ""
        return f"{self.base}{prop_str}"

    def depth(self) -> int:
        return len(self.base)


class Object:
    """Hierarchical representation of an image."""

    def __init__(
        self,
        row: int = 0,
        col: int = 0,
        color: int = cst.NULL_COLOR,
        children: list["Object"] | None = None,
        generator: Generator | None = None,
        row_bound: int = cst.MAX_ROWS,
        col_bound: int = cst.MAX_COLS,
        name: str = "",
        leaf: bool = False,
        process: str = "",
    ):
        self.row: int = row
        self.col: int = col
        self.color: int = color
        self.children: list["Object"] = children or []
        self.generator: Generator = generator or Generator([])
        self.row_bound: int = row_bound
        self.col_bound: int = col_bound

        # Utility attributes
        self.name: str = name

        # Attributes used during decomposition
        self.leaf: bool = leaf
        self.process: str = process

        # Attributes used during linking
        self.depth: int | None = None

        # WIP Integrate generation into Object
        self.codes: dict[str, int] = collections.defaultdict(int)

        if self.generator:
            for trans, copies in self.generator.rep:
                self.codes[trans.code] = copies

    ## Constructors
    @classmethod
    def from_grid(
        cls,
        grid: Grid | BoardData,
        anchor: Point = (0, 0, cst.NULL_COLOR),
        name: str = "",
        leaf: bool = False,
        process: str = "",
    ) -> "Object":
        grid = gridify(grid)
        if grid.size == 0:
            log.warning("empty obj")
            raise EmptyObject
        kwargs = {
            "name": name,
            "leaf": leaf,
            "process": process,
        }
        children: list[Object] = []
        M, N = grid.shape
        for i in range(M):
            for j in range(N):
                if grid[i, j] != cst.NULL_COLOR:
                    children.append(cls(i, j, grid[i, j]))
        return cls(*anchor, children=children, **kwargs)

    @classmethod
    def from_points(
        cls,
        points: PointList,
        loc: Position = (0, 0),
        name: str = "",
        leaf: bool = False,
        process: str = "",
    ) -> "Object":
        """Create an Object from a list of Points.

        This is used during Generator.materialize to efficiently generate the
        points belonging to resulting objects.
        """
        kwargs = {
            "name": name,
            "leaf": leaf,
            "process": process,
        }
        if len(points) == 0:
            log.warning("Empty from_points() constructor")
            raise EmptyObject
        elif len(points) == 1:
            return cls(*points[0], **kwargs)

        norm_loc, normed, monochrome = norm_points(points)
        loc = (loc[0] + norm_loc[0], loc[1] + norm_loc[1])
        if monochrome:
            children = [Object(*pt[:2]) for pt in normed]
            return cls(*loc, normed[0][2], children=children, **kwargs)
        else:
            children = [Object(*pt) for pt in normed]
            return cls(*loc, children=children, **kwargs)

    ## Core properties
    @property
    def loc(self) -> tuple[int, int]:
        """The *local* position of the Object."""
        return (self.row, self.col)

    @property
    def anchor(self) -> tuple[int, int, int]:
        """The *local* position and color information of the Object."""
        return (self.row, self.col, self.color)

    @cached_property
    def generating(self) -> bool:
        return any(val > 0 for val in self.codes.values())

    # NOTE: Keep an eye on the caching here to make sure it behaves appropriately
    @cached_property
    def materialized(self) -> "Object":
        if not self.generator:
            return self
        kernel = Object(
            color=self.color,
            children=[obj.materialized for obj in self.children],
        )
        new_obj = Object(*self.anchor, children=self.generator.materialize(kernel))
        return new_obj

    @cached_property
    def points(self) -> PointDict:
        """Dict of all points defined by the Object and its children."""
        if self.category == "Dot":
            return {(0, 0): self.color}

        pts: PointDict = {}
        if self.generator:
            pts.update(self.materialized.points)
        else:
            # NOTE The order of children determines layering, bottom first
            for child in self.children:
                for loc, val in child.points.items():
                    new_loc = (child.row + loc[0], child.col + loc[1])
                    if val == cst.NEGATIVE_COLOR:
                        pts.pop(new_loc, None)
                    elif val != cst.NULL_COLOR:
                        pts[new_loc] = int(val)
                    else:
                        pts[new_loc] = self.color

        for loc in list(pts.keys()):
            if loc[0] >= self.row_bound or loc[1] >= self.col_bound:
                pts.pop(loc)
        return pts

    @cached_property
    def locs(self) -> PositionList:
        """The list of coordinates relative to the object's anchor location"""
        return sorted(list(self.points.keys()))

    @cached_property
    def locs_abs(self) -> PositionList:
        """The list of coordinates in the parent's frame of reference."""
        return [(loc[0] + self.row, loc[1] + self.col) for loc in self.locs]

    @cached_property
    def grid(self) -> Grid:
        """2D grid of the object"""
        if self.category == "Dot":
            return gridify([[self.color]])
        _grid: Grid = gridify([[cst.NULL_COLOR]], self.shape)
        for pos, val in self.points.items():
            _grid[pos] = val
        return _grid

    @cached_property
    def size(self) -> int:
        return len(self.points)

    @cached_property
    def is_symm(self) -> bool:
        if (
            self.order_trans_col[1] == 1
            or self.order_trans_row[1] == 1
            or self.order_rotation[1] == 1
            or self.order_mirror[0] == 1
            or self.order_mirror[1] == 1
        ):
            return True
        else:
            return False

    @cached_property
    def symm(self) -> str:
        if self.order_trans_col[1] == 1 or self.order_trans_row[1] == 1:
            return "Translation"
        elif self.order_rotation[1] == 1:
            return "Rotation"
        elif self.order_mirror[0] == 1 or self.order_mirror[1] == 1:
            return "Mirror"
        return ""

    @cached_property
    def meta(self) -> str:
        if self.connectedness == 1:
            return "Blob"
        elif self.connectedness * 1.2 > self.size:
            return "Static"
        else:
            return "Normal"

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
                return "Pattern"
            elif self.process == "Cell":
                return "Cell"
            elif all([kid.category == "Dot" for kid in self.children]):
                return "Cluster"
            else:
                return "Container"

    @cached_property
    def shape(self) -> tuple[int, int]:
        """The bounding dimensions of the Object."""
        if self.category == "Dot":
            return (1, 1)
        if not self.points:
            log.warning("No points in object")
            raise EmptyObject
        maxrow = max([pos[0] for pos in self.points])
        maxcol = max([pos[1] for pos in self.points])
        return (maxrow + 1, maxcol + 1)

    @cached_property
    def area(self) -> int:
        return self.shape[0] * self.shape[1]

    @cached_property
    def width(self) -> int:
        return self.shape[0]

    @cached_property
    def height(self) -> int:
        return self.shape[1]

    @cached_property
    def bound_info(self) -> tuple[PointList, PositionList]:
        """Convenience property to support efficient processing."""
        return get_boundary(self.grid)

    @cached_property
    def boundary(self) -> PointList:
        """All points of the object that are reachable by STEPS_BASE from outside."""
        return self.bound_info[0]

    @cached_property
    def enclosed(self) -> PositionList:
        """All points not of the object not reachable by ALL_STEPS from outside."""
        return self.bound_info[1]

    @cached_property
    def blobs(self) -> list[PointList]:
        if len(self.points) == 1:
            return [[self.anchor]]
        marked = self.grid.copy()
        marked[marked == cst.NULL_COLOR] = cst.MARKED_COLOR
        return connect(marked)

    @cached_property
    def connectedness(self) -> int:
        return len(self.blobs)

    ## Comparisons
    def __eq__(self, other: "Object") -> bool:
        return self.loc == other.loc and self.sim(other)

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
        elif self.anchor != other.anchor:
            return self.anchor < other.anchor
        else:
            return False

    def issubset(self, other: "Object") -> bool:
        return set(self.points).issubset(other.points)

    ## Utility Methods
    def __getitem__(self, key: int) -> "Object":
        return self.children[key]

    @cached_property
    def uid(self) -> str:
        """Generate a unique ID for the object, used for Labeling."""
        # TODO Look into fixing this up
        # hasher = hashlib.sha1(str(uuid.uuid1()).encode())
        # return str(base64.urlsafe_b64decode(hasher.digest()))[:8]
        return str(int(uuid.uuid1()) % 1000000)

    #! Properties relying on the traits dictionary shouldn't be cached
    @property
    def id(self) -> str:
        """A concise, (nearly) unique description of the Object."""
        if self.category == "Dot":
            shape_str = ""
        else:
            shape_str = f"({self.shape[0]}x{self.shape[1]})"
        name = "" if not self.name else f" '{self.name}'"
        return f"{self.category}{shape_str}@{self.anchor}{name}"

    def __repr__(self) -> str:
        """One line description of what the object is"""
        if self.category == "Dot":
            info = ""
        else:
            info = f"({len(self.children)}ch, {self.size}pts, {self.props}p)"
        process = f"[{self.process}]" if self.process else ""
        return f"{process}{self.id}{info}"

    def hier_repr(self, tab: int = 0, max_lines: int = 10, max_dots: int = 5) -> str:
        """Detailed info on object and its children"""
        indent = "  " * tab
        output = [indent + self.__repr__()]

        if self.generator:
            output.append(f"{indent}  Generator{self.generator}")

        dot_kids = 0
        for child in self.children:
            if child.category == "Dot":
                dot_kids += 1
            if dot_kids < max_dots:
                output.append(
                    f"{child.hier_repr(tab=tab+1, max_lines=max_lines, max_dots=max_dots)}"
                )
        if dot_kids >= max_dots:
            output.append(f"{indent}  ...{dot_kids} Dots total")

        # Limit output to 'max_lines' by truncating remainder
        if len(output) > max_lines and "..." not in output:
            output = output[:max_lines] + ["..."]
        return "\n".join(output)

    def debug(self) -> None:
        """Print full hierarchy, gated behind a check to avoid CPU cost."""
        if log.level > 10:
            return
        log.debug(f"\n{self.hier_repr(max_lines=100, max_dots=100)}")

    def copy(
        self, anchor: tuple[int, int, int] | None = None, **kwargs: Any
    ) -> "Object":
        anchor = anchor or self.anchor
        if self.category == "Dot":
            return Object(*anchor)
        # Perhaps altering children isn't necessary in most cases
        new_args = {
            "children": [kid.copy() for kid in self.children],
            "generator": self.generator,
            "row_bound": self.row_bound,
            "col_bound": self.col_bound,
            "name": self.name,
            "leaf": self.leaf,
            "process": self.process,
        }
        new_args.update(kwargs)
        return Object(*anchor, **new_args)

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

        # Containers are flattenable: they have no generators, and have children
        if self.category != "Container":
            return self
        new_children: list[Object] = []
        for kid in self.children:
            flat_kid = kid.flatten()
            # We can't currently flatten containers with cutouts. Food for thought?
            if any([gkid.category == "Cutout" for gkid in flat_kid.children]):
                new_children.append(flat_kid)
                continue

            # We can't flatten through a generator
            if kid.generator:
                new_children.append(flat_kid)
                continue

            if len(flat_kid.children) == 1 or (
                flat_kid.category == "Container" and flat_kid.color == cst.NULL_COLOR
            ):
                uplevel: list[Object] = []
                for gkid in flat_kid.children:
                    row, col = gkid.row + kid.row, gkid.col + kid.col
                    uplevel.append(gkid.copy(anchor=(row, col, gkid.color)))
                new_children.extend(uplevel)
            else:
                new_children.append(flat_kid)
        return self.copy(self.anchor, children=new_children)

    def overlap(self, other: "Object") -> float:
        return grid_overlap(self.grid, other.grid)

    @cached_property
    def props(self) -> int:
        """Count how many properties are used in this Object representation.

        This is a core piece of information used to determine the "value" of
        a representation--the more compact the better. There is some leeway
        in this definition, which might be a central point of consideration
        for achieving success in applications.
        """
        # When we have a contextual reference, we already "know" the object
        # TODO The parameter count associated with 'reusing' an Object likely
        # needs to take more into account.
        if self.process == "Inv":
            return 1

        # Calculate local information used (self existence, positions, and color)
        from_pos = int(self.row != 0) + int(self.col != 0)
        own_props = from_pos + int(self.color != cst.NULL_COLOR)

        if self.category == "Dot":
            return cst.DOT_PROPS + own_props

        # TODO WIP Add a bias against Cutout, so small shapes don't overuse it
        if self.category == "Cutout":
            own_props += cst.CUTOUT_PROPS * self.size

        from_children = sum([item.props for item in self.children])
        from_gen = 0 if not self.generator else self.generator.props
        return cst.NON_DOT_PROPS + own_props + from_gen + from_children

    @cached_property
    def c_rank(self) -> list[tuple[int, int]]:
        """Get the counts for each color on the grid, starting with most prevalent"""
        counter = collections.Counter(self.points.values())
        return sorted(counter.items(), key=lambda x: (x[1], x[0]), reverse=True)

    @cached_property
    def order_trans_row(self) -> tuple[int, float]:
        if self.category == "Dot":
            return (1, 1)
        return translational_order(self.grid, row_axis=True)[0]

    @cached_property
    def order_trans_col(self) -> tuple[int, float]:
        if self.category == "Dot":
            return (1, 1)
        return translational_order(self.grid, row_axis=False)[0]

    @cached_property
    def order_mirror(self) -> tuple[float, float]:
        """Determine symmetry across axial grid reflections."""
        if self.category == "Dot":
            return (0, 0)
        row_o = mirror_order(self.grid, row_axis=True)
        col_o = mirror_order(self.grid, row_axis=False)
        return (row_o, col_o)

    @cached_property
    def order_rotation(self) -> tuple[int, float]:
        """Determine symmetry through rotations."""
        if self.category == "Dot":
            return (0, 0)
        return rotational_order(self.grid)

    def get_path(self, path: BaseObjectPath) -> "Object | None":
        result = self
        for child_idx in path:
            try:
                result = result.children[child_idx]
            except:
                log.warning(f"Can't access path {path} in {self}")
                return None
        return result

    def get_value(self, path: ObjectPath) -> int | None:
        target = self.get_path(path.base)
        if target and isinstance(path.property, str):
            if len(path.property) == 1:
                return target.codes[path.property]
            else:
                return getattr(target, path.property)

        return None


def sort_layer(objects: list[Object]) -> list[Object]:
    return list(sorted(objects, key=lambda x: (-x.size, x.row, x.col)))
