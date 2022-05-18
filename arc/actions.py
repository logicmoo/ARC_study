from typing import TYPE_CHECKING

import numpy as np

from arc.object_relations import chebyshev_vector

if TYPE_CHECKING:
    from arc.types import Grid
    from arc.object import Object


class Action:
    action_map = {
        "": "identity",
        "c": "recolor",
        "w": "vertical",
        "s": "horizontal",
        "f": "r_scale",  # 'flatten'
        "p": "c_scale",  # 'pinch'
        "M": "mtile",
        "R": "rtile",
        "C": "ctile",
        "S": "resize",
        "A": "adjoin",
        "L": "align",
        "t": "turn",
        "r": "flip",
        "|": "flip_h",
        "_": "flip_v",
        "V": "flip_tile_even_v",
        "H": "flip_tile_even_h",
        "v": "flip_tile_odd_v",
        "h": "flip_tile_odd_h",
        "O": "r90_tile_even",
        "U": "r180_tile_even",
        "j": "justify",
        "z": "zero",
    }

    def __init__(self) -> None:
        self.rev_map = {val: key for key, val in self.action_map.items()}

    @classmethod
    def __getitem__(cls, code: str):
        return getattr(cls, cls.action_map[code])

    ## TRANSLATION
    # Simple translations building on a 'move' method
    @classmethod
    def identity(cls, object: "Object") -> "Object":
        """Return a copy of the object."""
        return object.copy()

    @classmethod
    def move(cls, object: "Object", dr: int, dc: int) -> "Object":
        """Return a new Object/Shape with transformed coordinates"""
        a_row, a_col, color = object.anchor
        return object.copy((a_row + dr, a_col + dc, color))

    @classmethod
    def vertical(cls, object: "Object", value: int) -> "Object":
        return cls.move(object, value, 0)

    @classmethod
    def horizontal(cls, object: "Object", value: int) -> "Object":
        return cls.move(object, 0, value)

    # Translations built on moving past the edge of the object
    @classmethod
    def mtile(cls, object: "Object", nr: int, nc: int) -> "Object":
        dr, dc = object.shape
        return cls.move(object, nr * dr, nc * dc)

    @classmethod
    def rtile(cls, object: "Object") -> "Object":
        return cls.mtile(object, 1, 0)

    @classmethod
    def ctile(cls, object: "Object") -> "Object":
        return cls.mtile(object, 0, 1)

    # Translations using zeros
    @classmethod
    def zero(cls, object: "Object") -> "Object":
        """Set row and column to zero"""
        return object.copy((0, 0, object.color))

    @classmethod
    def justify(cls, object: "Object", axis: int) -> "Object":
        """Set one of row or column to zero"""
        loc = list(object.loc)
        loc[axis] = 0
        return object.copy((*loc, object.color))

    ## DEFORMATIONS
    # Linear transform along an axis
    @classmethod
    def scale(cls, object: "Object", code: str, value: int) -> "Object":
        """Change the value associated with a generator"""
        if not object.generator:
            return object.copy()
        copies = object.generator.copies.copy()
        for idx, trans in enumerate(object.generator.transforms):
            if trans.char == code:
                copies[idx] = value
        return object.copy(generator=object.generator.copy(copies=copies))

    @classmethod
    def r_scale(cls, object: "Object", value: int) -> "Object":
        return cls.scale(object, "R", value)

    @classmethod
    def c_scale(cls, object: "Object", value: int) -> "Object":
        return cls.scale(object, "C", value)

    ## ROTATIONS AND REFLECTIONS
    @classmethod
    def turn(cls, object: "Object", num: int) -> "Object":
        turned = object.grid
        for _ in range(num):
            turned: Grid = np.rot90(turned)  # type: ignore
        return object.__class__.from_grid(grid=turned, anchor=object.anchor)

    @classmethod
    def r90_tile_even(cls, object: "Object", row: int, col: int) -> "Object":
        # TODO This currently takes two args that are a reference row, col.
        # This position represents the axis of rotation (into the 2D plane)
        # It gets populated via the Generator "default args", which is a bit
        # of a hacked solution, perhaps.
        turned = cls.turn(object, 1)
        if row > object.row:
            return cls.rtile(turned)
        elif col > object.col:
            return cls.ctile(turned)
        else:
            return cls.mtile(turned, -1, 0)

    @classmethod
    def r180_tile_even(cls, object: "Object") -> "Object":
        turned = cls.turn(object, 2)
        return cls.ctile(cls.rtile(turned))

    @classmethod
    def flip(cls, object: "Object", axis: int) -> "Object":
        """Flip the object via the specified axis."""
        grid: Grid = np.flip(object.grid, axis)  # type: ignore
        return object.__class__.from_grid(grid=grid, anchor=object.anchor)

    @classmethod
    def flip_v(cls, object: "Object") -> "Object":
        return cls.flip(object, 0)

    @classmethod
    def flip_h(cls, object: "Object") -> "Object":
        return cls.flip(object, 1)

    @classmethod
    def flip_tile_even_v(cls, object: "Object") -> "Object":
        return cls.vertical(cls.flip(object, 0), object.shape[0])

    @classmethod
    def flip_tile_even_h(cls, object: "Object") -> "Object":
        return cls.horizontal(cls.flip(object, 1), object.shape[1])

    @classmethod
    def flip_tile_odd_v(cls, object: "Object") -> "Object":
        return cls.vertical(cls.flip(object, 0), object.shape[0] - 1)

    @classmethod
    def flip_tile_odd_h(cls, object: "Object") -> "Object":
        return cls.horizontal(cls.flip(object, 1), object.shape[1] - 1)

    ## COLOR
    @classmethod
    def recolor(cls, object: "Object", color: int) -> "Object":
        return object.copy(anchor=(*object.loc, color))

    ## 2-OBJECT ACTIONS
    # These actions leverage another object as the source of information
    # on how to transform the primary object.
    @classmethod
    def resize(cls, object: "Object", secondary: "Object") -> "Object":
        """Alter the primary object so its shape matches the secondary."""
        result = object.copy()
        if object.shape[0] != secondary.shape[0]:
            result = cls.r_scale(result, secondary.shape[0] - 1)
        if object.shape[1] != secondary.shape[1]:
            result = cls.c_scale(result, secondary.shape[1] - 1)
        return result

    @classmethod
    def adjoin(cls, object: "Object", secondary: "Object") -> "Object":
        """Move the primary in one direction towards the secondary.

        The primary will not intersect the secondary.
        """
        # Find the direction of smallest Chebyshev distance
        result = object.copy()
        ch_vector = chebyshev_vector(object, secondary)
        if ch_vector[0]:
            result = Action().vertical(result, ch_vector[0])
        elif ch_vector[1]:
            result = Action().horizontal(result, ch_vector[1])
        return result

    @classmethod
    def align(cls, object: "Object", secondary: "Object") -> "Object":
        """Move the primary the smallest amount to align on an axis with secondary."""
        result = object.copy()
        ch_vector = chebyshev_vector(object, secondary)
        if ch_vector[0]:
            sign = -1 if ch_vector[0] < 0 else 1
            result = Action().vertical(result, ch_vector[0] + sign * object.shape[0])
        elif ch_vector[1]:
            sign = -1 if ch_vector[1] < 0 else 1
            result = Action().horizontal(result, ch_vector[1] + sign * object.shape[1])
        return result


# A list of pairs of action sets, where the first actions might be
# substituted by the second action as a 2-object function
# TODO WIP
pair_actions = [Action.adjoin, Action.align, Action.resize]
subs = [("fp", "S"), ("ws", "AL")]
degeneracies = [{"|", "_", "t"}]
