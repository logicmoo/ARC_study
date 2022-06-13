from typing import TYPE_CHECKING

import numpy as np

from arc.definitions import Constants as cst
from arc.object_relations import chebyshev_vector
from arc.types import Args, Grid
from arc.util.common import Representation

if TYPE_CHECKING:
    from arc.object import Object


class DeterminantError(Exception):
    pass


class Action(metaclass=Representation):
    code: str = ""
    dimension: str = ""
    args: Args = tuple([])
    hot_arg: int = 0
    n_args: int = 0

    @classmethod
    def act(cls, object: "Object", *args: "int | Object") -> "Object":
        """Return a copy of the object with any logic applied."""
        return object.copy()

    @classmethod
    def inv(cls, left: "Object", right: "Object") -> Args:
        """Detect if this action helps relate two objects."""
        return tuple([])


class Pairwise:
    @classmethod
    def act(cls, object: "Object", secondary: "Object") -> "Object":
        """Return a copy of the object with any logic applied."""
        return object.copy()


class Actions:
    map: dict[str, type[Action]] = {}

    @classmethod
    def __getitem__(cls, code: str) -> type[Action]:
        return cls.map[code]

    ## COLOR

    class Paint(Action):
        dimension = "Color"
        n_args = 1

        @classmethod
        def act(cls, object: "Object", color: int = cst.NULL_COLOR) -> "Object":
            if color == cst.NULL_COLOR:
                return object.copy()
            return object.copy(anchor=(*object.loc, color))

        @classmethod
        def inv(cls, left: "Object", right: "Object") -> Args:
            c1 = set([item[0] for item in left.c_rank])
            c2 = set([item[0] for item in right.c_rank])
            if len(c1) == 1 and len(c2) == 1:
                if c1 != c2:
                    return (list(c2)[0],)
            return tuple([])

    ## LOCATION

    class Translate(Action):
        dimension = "Length"
        n_args = 2

        @classmethod
        def act(cls, object: "Object", dr: int = 0, dc: int = 0) -> "Object":
            """Return a new Object/Shape with transformed coordinates"""
            a_row, a_col, color = object.anchor
            return object.copy((a_row + dr, a_col + dc, color))

        @classmethod
        def inv(cls, left: "Object", right: "Object") -> Args:
            if left.loc == right.loc:
                return tuple([])
            return (right.row - left.row, right.col - left.col)

    class Vertical(Translate):
        hot_arg = 1
        n_args = 1

        @classmethod
        def act(cls, object: "Object", dr: int = 0) -> "Object":
            return super().act(object, dr, 0)

    class Horizontal(Translate):
        hot_arg = 0
        n_args = 1

        @classmethod
        def act(cls, object: "Object", dc: int = 0) -> "Object":
            return super().act(object, 0, dc)

    class Tile(Translate):
        """Translate based on the object's shape."""

        n_args = 2

        @classmethod
        def act(cls, object: "Object", nr: int = 0, nc: int = 0) -> "Object":
            dr, dc = object.shape
            return super().act(object, nr * dr, nc * dc)

    class VTile(Tile):
        hot_arg = 1
        n_args = 1

        @classmethod
        def act(cls, object: "Object") -> "Object":
            return super().act(object, 1, 0)

    class HTile(Tile):
        hot_arg = 0
        n_args = 1

        @classmethod
        def act(cls, object: "Object") -> "Object":
            return super().act(object, 0, 1)

    class Justify(Translate):
        """Set one of row or column to zero."""

        n_args = 1

        @classmethod
        def act(cls, object: "Object", axis: int) -> "Object":
            if axis == 0:
                return super().act(object, -object.row, 0)
            else:
                return super().act(object, 0, -object.col)

    class Zero(Justify):
        """Set row and column to zero."""

        n_args = 0

        @classmethod
        def act(cls, object: "Object") -> "Object":
            return object.copy((0, 0, object.color))

    ## ORTHOGONAL OPS: ROTATIONS AND REFLECTIONS
    class Orthogonal(Action):
        """The group of 2D orthogonal operations, args representing the matrix."""

        n_args = 2
        o_arg = 0

        # TODO WIP
        @classmethod
        def act(
            cls, object: "Object", reflection: int = 0, rotation: int = 0
        ) -> "Object":
            result = object.copy()
            if reflection == 1:
                result = Actions.VFlip.act(result)
            elif reflection == 2:
                result = Actions.HFlip.act(result)
            if rotation > 0:
                result = Actions.Rotate.act(result, rotation)
            return result

        @classmethod
        def inv(cls, left: "Object", right: "Object") -> Args:
            if left.c_rank != right.c_rank:
                return tuple([])

            for reflection in (cls, Actions.VFlip, Actions.HFlip):
                if (reflected := reflection.act(left)) == right:
                    return (reflection.o_arg, 0)
                for ct in [1, 2, 3]:
                    if Actions.Rotate.act(reflected, ct) == right:
                        return (reflection.o_arg, ct)
            return tuple([])

    class Rotate(Orthogonal):
        n_args = 1
        hot_arg = 1

        @classmethod
        def act(cls, object: "Object", num: int) -> "Object":
            turned = object.grid
            for _ in range(num):
                turned: Grid = np.rot90(turned)  # type: ignore
            return object.__class__.from_grid(grid=turned, anchor=object.anchor)

    class Flip(Orthogonal):
        n_args = 1
        hot_arg = 0

        @classmethod
        def act(cls, object: "Object", horizontal: int) -> "Object":
            """Flip the object via the specified axis."""
            grid: Grid = np.flip(object.grid, horizontal)  # type: ignore
            return object.__class__.from_grid(grid=grid, anchor=object.anchor)

    class VFlip(Flip):
        n_args = 0
        o_arg = 1

        @classmethod
        def act(cls, object: "Object") -> "Object":
            return super().act(object, 0)

    class HFlip(Flip):
        n_args = 0
        o_arg = 2

        @classmethod
        def act(cls, object: "Object") -> "Object":
            return super().act(object, 1)

    ## DEFORMATIONS
    class Scale(Action):
        n_args = 2

        @classmethod
        def act(cls, object: "Object", vertical: int, horizontal: int) -> "Object":
            """Change the value associated with a generating code"""
            updated_codes = object.codes.copy()
            if vertical > 0:
                updated_codes["V"] = vertical - 1
            if horizontal > 0:
                updated_codes["H"] = horizontal - 1
            return object.copy(codes=updated_codes)

        @classmethod
        def inv(cls, left: "Object", right: "Object") -> Args:
            args = tuple([])
            for axis, code in [(0, "V"), (1, "H")]:
                if left.shape[axis] != right.shape[axis]:
                    cell = left.shape[axis] // (left.codes[code] + 1)
                    if right.shape[axis] % cell:
                        # Incommensurate shapes
                        continue
                    new_value = right.shape[axis] // cell
                    args += (new_value,)
            return args

    class VScale(Scale):
        n_args = 1

        @classmethod
        def act(cls, object: "Object", value: int) -> "Object":
            return super().act(object, value, 0)

    class HScale(Scale):
        n_args = 1

        @classmethod
        def act(cls, object: "Object", value: int) -> "Object":
            return super().act(object, 0, value)

    ## 2-OBJECT ACTIONS
    # These actions leverage another object as the source of information
    # on how to transform the primary object.
    class Resize(Pairwise, Scale):
        n_args = 1

        @classmethod
        def act(cls, object: "Object", secondary: "Object") -> "Object":
            """Alter the main object so its shape matches the secondary."""
            result = object.copy()
            if object.shape[0] != secondary.shape[0]:
                result = Actions.Scale.act(result, secondary.shape[0], 0)
            if object.shape[1] != secondary.shape[1]:
                result = Actions.Scale.act(result, 0, secondary.shape[1])
            return result

    class Adjoin(Pairwise, Translate):
        n_args = 1

        @classmethod
        def act(cls, object: "Object", secondary: "Object") -> "Object":
            """Translate the main object in one direction towards the secondary.

            The primary will not intersect the secondary.
            """
            # Find the direction of smallest Chebyshev distance
            result = object.copy()
            ch_vector = chebyshev_vector(object, secondary)
            if ch_vector[0]:
                result = Actions.Translate.act(result, ch_vector[0], 0)
            elif ch_vector[1]:
                result = Actions.Translate.act(result, 0, ch_vector[1])
            return result

    class Align(Pairwise, Translate):
        n_args = 1

        @classmethod
        def act(cls, object: "Object", secondary: "Object") -> "Object":
            """Translate the main object to the nearest alignment to secondary."""
            result = object.copy()
            ch_vector = chebyshev_vector(object, secondary)
            if ch_vector[0]:
                sign = -1 if ch_vector[0] < 0 else 1
                result = Actions.Translate.act(
                    result, ch_vector[0] + sign * object.shape[0], 0
                )
            elif ch_vector[1]:
                sign = -1 if ch_vector[1] < 0 else 1
                result = Actions.Translate.act(
                    result, 0, ch_vector[1] + sign * object.shape[1]
                )
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

    class RotTile(Actions.Rotate, Actions.Tile):
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
    "": Action,
    # Color
    "c": Actions.Paint,
    # Location
    "t": Actions.Translate,
    "v": Actions.Vertical,
    "h": Actions.Horizontal,
    "T": Actions.Tile,
    "V": Actions.VTile,
    "H": Actions.HTile,
    "j": Actions.Justify,
    "z": Actions.Zero,
    # Orientation
    "o": Actions.Orthogonal,
    "r": Actions.Rotate,
    "+": Actions.Flip,
    "|": Actions.HFlip,
    "_": Actions.VFlip,
    # Deformation
    "s": Actions.Scale,
    "f": Actions.VScale,  # flatten
    "p": Actions.HScale,  # pinch
    # Pair
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
