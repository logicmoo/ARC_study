from typing import TYPE_CHECKING

import numpy as np


if TYPE_CHECKING:
    from arc.object import Object
    from arc.generator import Transform


class Action:
    action_map = {
        "c": "recolor",
        "w": "vertical",
        "s": "sideways",
        "f": "r_scale",  # 'flatten'
        "p": "c_scale",  # 'pinch'
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
        action = Action()[code]
        new_transforms: list["Transform"] = []
        for trans in object.generator.transforms:
            # TODO This is temporary, it will only work with single char gens
            if len(trans.actions) == 1 and trans.actions[0] == action:
                new_transforms.append(trans.__class__(trans.actions, value))
            else:
                new_transforms.append(trans.spawn())
        return object.spawn(generator=object.generator.__class__(new_transforms))

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
        for i in range(num):
            turned = np.rot90(turned)
        return object.__class__.from_grid(grid=turned, anchor=object.anchor)

    @classmethod
    def flip(cls, object: "Object", axis: int) -> "Object":
        """Flip the object via the specified axis."""
        grid = np.flip(object.grid, axis)
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
