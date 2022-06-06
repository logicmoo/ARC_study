from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np

from arc.object_relations import chebyshev_vector
from arc.types import Args

if TYPE_CHECKING:
    from arc.types import Grid
    from arc.object import Object


class Action(ABC):
    code: str = ""
    dimension: str = ""
    n_args: int = 0

    @classmethod
    @abstractmethod
    def act(cls, object: "Object") -> "Object":
        """Return a copy of the object with any logic applied."""
        return object.copy()

    @classmethod
    @abstractmethod
    def inv(cls, left: "Object", right: "Object") -> Args | None:
        """Detect if this action helps relate two objects."""
        return None


class Actions:
    map: dict[str, type[Action]] = {}

    @classmethod
    def __getitem__(cls, code: str) -> type[Action]:
        return cls.map[code]

    class Identity(Action):
        @classmethod
        def act(cls, object: "Object") -> "Object":
            return object.copy()

        @classmethod
        def inv(cls, left: "Object", right: "Object") -> Args | None:
            return tuple([])

    ## Color

    class Paint(Action):
        @classmethod
        def act(cls, object: "Object", color: int) -> "Object":
            return object.copy(anchor=(*object.loc, color))

        @classmethod
        def inv(cls, left: "Object", right: "Object") -> Args | None:
            c1 = set([item[0] for item in left.c_rank])
            c2 = set([item[0] for item in right.c_rank])
            if c1 != c2 and len(c1) == 1 and len(c2) == 1:
                return (list(c2)[0],)

    ## Location

    class Translate(Action):
        @classmethod
        def act(cls, object: "Object", dr: int, dc: int) -> "Object":
            """Return a new Object/Shape with transformed coordinates"""
            a_row, a_col, color = object.anchor
            return object.copy((a_row + dr, a_col + dc, color))

        @classmethod
        def inv(cls, left: "Object", right: "Object") -> Args | None:
            return (right.row - left.row, right.col - left.col)

    class Vertical(Translate):
        @classmethod
        def act(cls, object: "Object", dr: int) -> "Object":
            return super().act(object, dr, 0)

    class Horizontal(Translate):
        @classmethod
        def act(cls, object: "Object", dc: int) -> "Object":
            return super().act(object, 0, dc)

    class Tile(Translate):
        """Translate based on the object's shape."""

        @classmethod
        def act(cls, object: "Object", nr: int, nc: int) -> "Object":
            dr, dc = object.shape
            return super().act(object, nr * dr, nc * dc)

    class VTile(Tile):
        @classmethod
        def act(cls, object: "Object") -> "Object":
            return super().act(object, 1, 0)

    class HTile(Tile):
        @classmethod
        def act(cls, object: "Object") -> "Object":
            return super().act(object, 0, 1)

    class Justify(Translate):
        """Set one of row or column to zero."""

        @classmethod
        def act(cls, object: "Object", axis: int) -> "Object":
            if axis == 0:
                return super().act(object, -object.row, 0)
            else:
                return super().act(object, 0, -object.col)

    class Zero(Justify):
        """Set row and column to zero."""

        @classmethod
        def act(cls, object: "Object") -> "Object":
            return object.copy((0, 0, object.color))

    ## Generator
    class Scale(Action):
        @classmethod
        def act(cls, object: "Object", code: str, value: int) -> "Object":
            """Change the value associated with a generating code"""
            if not object.generating:
                return object.copy()
            updated_codes = object.codes.copy()
            updated_codes[code] = value
            return object.copy(codes=updated_codes)

        @classmethod
        def inv(cls, left: "Object", right: "Object") -> Args | None:
            if len(left.c_rank) == 1 and len(right.c_rank) == 1:
                # A monochrome, matching silhouette means no internal positioning differences
                if left.sil(right):
                    return tuple([])

            # TODO
            # There could exist one or more generators to create the other object
            args = tuple([])
            for axis in [0, 1]:
                if left.shape[axis] != right.shape[axis]:
                    ct = right.shape[axis] - 1
                    args += (ct,)
            return args

    class VScale(Scale):
        @classmethod
        def act(cls, object: "Object", value: int) -> "Object":
            return super().act(object, "V", value)

    class HScale(Scale):
        @classmethod
        def act(cls, object: "Object", value: int) -> "Object":
            return super().act(object, "H", value)

    ## ROTATIONS AND REFLECTIONS
    class Turn(Action):
        @classmethod
        def act(cls, object: "Object", num: int) -> "Object":
            turned = object.grid
            for _ in range(num):
                turned: Grid = np.rot90(turned)  # type: ignore
            return object.__class__.from_grid(grid=turned, anchor=object.anchor)

    class Flip(Action):
        @classmethod
        def act(cls, object: "Object", axis: int) -> "Object":
            """Flip the object via the specified axis."""
            grid: Grid = np.flip(object.grid, axis)  # type: ignore
            return object.__class__.from_grid(grid=grid, anchor=object.anchor)

    class VFlip(Flip):
        @classmethod
        def act(cls, object: "Object") -> "Object":
            return super().act(object, 0)

    class HFlip(Flip):
        @classmethod
        def act(cls, object: "Object") -> "Object":
            return super().act(object, 1)

    ## 2-OBJECT ACTIONS
    # These actions leverage another object as the source of information
    # on how to transform the primary object.
    class Resize(Scale):
        @classmethod
        def act(cls, object: "Object", secondary: "Object") -> "Object":
            """Alter the primary object so its shape matches the secondary."""
            result = object.copy()
            if object.shape[0] != secondary.shape[0]:
                result = super().act(result, "V", secondary.shape[0] - 1)
            if object.shape[1] != secondary.shape[1]:
                result = super().act(result, "H", secondary.shape[1] - 1)
            return result

    class Adjoin(Translate):
        @classmethod
        def act(cls, object: "Object", secondary: "Object") -> "Object":
            """Translate the primary in one direction towards the secondary.

            The primary will not intersect the secondary.
            """
            # Find the direction of smallest Chebyshev distance
            result = object.copy()
            ch_vector = chebyshev_vector(object, secondary)
            if ch_vector[0]:
                result = super().act(result, ch_vector[0], 0)
            elif ch_vector[1]:
                result = super().act(result, 0, ch_vector[1])
            return result

    class Align(Translate):
        @classmethod
        def act(cls, object: "Object", secondary: "Object") -> "Object":
            """Translate the primary the smallest amount to align on an axis with secondary."""
            result = object.copy()
            ch_vector = chebyshev_vector(object, secondary)
            if ch_vector[0]:
                sign = -1 if ch_vector[0] < 0 else 1
                result = super().act(result, ch_vector[0] + sign * object.shape[0], 0)
            elif ch_vector[1]:
                sign = -1 if ch_vector[1] < 0 else 1
                result = super().act(result, 0, ch_vector[1] + sign * object.shape[1])
            return result


class Compounds:
    ## Combination Flip and Translation
    class VFlipTile(Actions.VFlip, Actions.VTile):
        @classmethod
        def act(cls, object: "Object") -> "Object":
            return Actions.VTile.act(Actions.VFlip.act(object))

    class HFlipTile(Actions.HFlip, Actions.HTile):
        @classmethod
        def act(cls, object: "Object") -> "Object":
            return Actions.HTile.act(Actions.HFlip.act(object))

    class VFlipHinge(Actions.VFlip, Actions.Vertical):
        @classmethod
        def act(cls, object: "Object") -> "Object":
            return Actions.Vertical.act(Actions.VFlip.act(object), object.shape[0] - 1)

    class HFlipHinge(Actions.HFlip, Actions.Horizontal):
        @classmethod
        def act(cls, object: "Object") -> "Object":
            return Actions.Horizontal.act(
                Actions.HFlip.act(object), object.shape[1] - 1
            )

    class RotTile(Actions.Turn, Actions.Tile):
        @classmethod
        def act(cls, object: "Object") -> "Object":
            # TODO This currently takes two args that are a reference row, col.
            # This position represents the axis of rotation (into the 2D plane)
            # It gets populated via the Generator "default args", which is a bit
            # of a hacked solution, perhaps.
            turned = super().act(object, 1)
            if object.height > object.row:
                return Actions.Tile.act(turned, 1, 0)
            elif object.width > object.col:
                return Actions.Tile.act(turned, 0, 1)
            else:
                return Actions.Tile.act(turned, -1, 0)


action_map: dict[str, type[Action]] = {
    "": Actions.Identity,
    "c": Actions.Paint,  # color
    "t": Actions.Translate,
    "v": Actions.Vertical,
    "h": Actions.Horizontal,
    "T": Actions.Tile,
    "V": Actions.VTile,
    "H": Actions.HTile,
    "j": Actions.Justify,
    "z": Actions.Zero,
    "f": Actions.VScale,  # flatten
    "p": Actions.HScale,  # pinch
    "t": Actions.Turn,
    "+": Actions.Flip,
    "|": Actions.HFlip,
    "_": Actions.VFlip,
    "S": Actions.Resize,
    "A": Actions.Adjoin,
    "L": Actions.Align,
    # Compound
    "m": Compounds.VFlipHinge,
    "M": Compounds.VFlipTile,
    "e": Compounds.HFlipHinge,
    "E": Compounds.HFlipTile,
    "O": Compounds.RotTile,
}

for code, action in action_map.items():
    action.code = code
    Actions.map[code] = action

# TODO Add a mixin to handle additional Action properties
pair_actions = [Actions.Adjoin, Actions.Align, Actions.Resize]
subs = [("fp", "S"), ("vh", "AL")]
degeneracies = [{"|", "_", "t"}, {"", "z"}]
