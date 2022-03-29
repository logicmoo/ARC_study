from typing import TYPE_CHECKING

import numpy as np


if TYPE_CHECKING:
    from arc.types import Grid
    from arc.object import Object


## Helper methods
# TODO: Find a better solution for these?
def chebyshev_vector(left: "Object", right: "Object") -> tuple[int, int]:
    left_min_row, left_min_col = left.loc
    left_max_row = left.row + left.shape[0]
    left_max_col = left.col + left.shape[1]

    right_min_row, right_min_col = right.loc
    right_max_row = right.row + right.shape[0]
    right_max_col = right.col + right.shape[1]

    dist: list[int | None] = [None, None]
    # Check for any horizontal overlap
    if left_min_row >= right_max_row:
        dist[0] = right_max_row - left_min_row
    elif left_max_row <= right_min_row:
        dist[0] = right_min_row - left_max_row
    # Check for any vertical overlap
    if left_min_col >= right_max_col:
        dist[1] = right_max_col - left_min_col
    elif left_max_col <= right_min_col:
        dist[1] = right_min_col - left_max_col

    match dist:
        # Objects' bounding boxes overlap
        case [None, None]:
            return (0, 0)
        case [int(row_dist), None]:
            return (row_dist, 0)
        case [None, int(col_dist)]:
            return (0, col_dist)
        case [int(row_dist), int(col_dist)]:
            if abs(col_dist) > abs(row_dist):
                return (row_dist, 0)
            else:
                return (0, col_dist)
        case _:  # pragma: no cover
            return (0, 0)


class Action:
    action_map = {
        "c": "recolor",
        "w": "vertical",
        "s": "horizontal",
        "f": "r_scale",  # 'flatten'
        "p": "c_scale",  # 'pinch'
        "M": "mtile",
        "R": "rtile",
        "C": "ctile",
        "t": "turn",
        "r": "right",
        "l": "left",
        "d": "down",
        "u": "up",
        "h": "flip_h",
        "v": "flip_v",
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
    def move(cls, object: "Object", dr: int, dc: int) -> "Object":
        """Returns a new Object/Shape with transformed coordinates"""
        a_row, a_col, color = object.anchor
        return object.spawn((a_row + dr, a_col + dc, color))

    @classmethod
    def vertical(cls, object: "Object", value: int) -> "Object":
        return cls.move(object, value, 0)

    @classmethod
    def horizontal(cls, object: "Object", value: int) -> "Object":
        return cls.move(object, 0, value)

    @classmethod
    def up(cls, object: "Object") -> "Object":
        return cls.vertical(object, -1)

    @classmethod
    def down(cls, object: "Object") -> "Object":
        return cls.vertical(object, 1)

    @classmethod
    def left(cls, object: "Object") -> "Object":
        return cls.horizontal(object, -1)

    @classmethod
    def right(cls, object: "Object") -> "Object":
        return cls.horizontal(object, 1)

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
        """Sets row and column to zero"""
        return object.spawn((0, 0, object.color))

    @classmethod
    def justify(cls, object: "Object", axis: int) -> "Object":
        """Sets one of row or column to zero"""
        loc = list(object.loc)
        loc[axis] = 0
        return object.spawn((*loc, object.color))

    ## DEFORMATIONS
    # Linear transform along an axis
    @classmethod
    def scale(cls, object: "Object", code: str, value: int) -> "Object":
        """Changes the value associated with a generator"""
        if not object.generator:
            return object.spawn()
        copies = object.generator.copies.copy()
        for idx, trans in enumerate(object.generator.transforms):
            if trans.char == code:
                copies[idx] = value
        return object.spawn(generator=object.generator.spawn(copies=copies))

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

    ## COLOR
    @classmethod
    def recolor(cls, object: "Object", color: int) -> "Object":
        return object.spawn(anchor=(*object.loc, color))

    ## 2-OBJECT ACTIONS
    # These actions leverage another object as the source of information
    # on how to transform the primary object.
    @classmethod
    def resize(cls, object: "Object", secondary: "Object") -> "Object":
        """Alter the primary object so its shape matches the secondary."""
        result = object.spawn()
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
        result = object.spawn()
        ch_vector = chebyshev_vector(object, secondary)
        if ch_vector[0]:
            result = Action().vertical(result, ch_vector[0])
        elif ch_vector[1]:
            result = Action().horizontal(result, ch_vector[1])
        return result
