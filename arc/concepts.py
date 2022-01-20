from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from arc.object import Object


class Action:
    action_map = {
        "c": "recolor",
        "w": "vertical",
        "s": "sideways",
        "f": "flatten",
        "p": "pinch",
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
    def __getitem__(cls, code):
        return getattr(cls, cls.action_map[code])

    @classmethod
    def move(cls, item: "Object", dr: int, dc: int) -> "Object":
        """Returns a new Object/Shape with transformed coordinates"""
        a_row, a_col, color = item.seed
        return item.spawn((a_row + dr, a_col + dc, color))

    @classmethod
    def mtile(cls, item, nr, nc):
        a_row, a_col, color = item.seed
        dr, dc = item.shape
        args = (a_row + nr * dr, a_col + nc * dc, color)
        return item.spawn(args)

    @classmethod
    def zero(cls, item, dummy=0):
        """Sets row and column to zero"""
        return item.spawn(row=0, col=0)

    @classmethod
    def justify(cls, item, axis):
        """Sets one of row or column to zero"""
        loc = list(item.loc)
        loc[axis] = 0
        return item.spawn(*loc)

    @classmethod
    def rescale(cls, item, code, value):
        """Changes the value associated with a translational generator"""
        new_gens = []
        for gen in item.gens:
            # TODO This is temporary, it will only work with single char gens
            if gen[0] == code:
                new_gens.append(f"{code}{value}")
            else:
                new_gens.append(gen)
        return item.spawn(gens=new_gens)

    @classmethod
    def flatten(cls, item, value):
        return cls.rescale(item, "R", value)

    @classmethod
    def pinch(cls, item, value):
        return cls.rescale(item, "C", value)

    @classmethod
    def turn(cls, item, num):
        turned = item
        for i in range(num):
            turned = np.rot90(item.grid)
        return item.__class__(grid=turned)

    @classmethod
    def flip(cls, item, axis):
        """Copies and flips the item across the specified axis"""
        loc = list(item.loc)
        loc[axis] += item.shape[axis]
        grid = np.flip(item.grid, axis)
        return item.__class__(*loc, grid=grid)

    @classmethod
    def recolor(cls, item, color):
        return item.spawn(color=color)

    @classmethod
    def vertical(cls, item, value):
        return cls.move(item, value, 0)

    @classmethod
    def sideways(cls, item, value):
        return cls.move(item, 0, value)

    @classmethod
    def left(cls, item):
        return cls.move(item, 0, -1)

    @classmethod
    def right(cls, item):
        return cls.move(item, 0, 1)

    @classmethod
    def up(cls, item):
        return cls.move(item, -1, 0)

    @classmethod
    def down(cls, item):
        return cls.move(item, 1, 0)

    @classmethod
    def rtile(cls, item):
        return cls.mtile(item, 1, 0)

    @classmethod
    def ctile(cls, item):
        return cls.mtile(item, 0, 1)

    @classmethod
    def flip_v(cls, item):
        return cls.flip(item, 0)

    @classmethod
    def flip_h(cls, item):
        return cls.flip(item, 1)
