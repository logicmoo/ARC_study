"""The Transform class handles mutations of objects.

We assume that the simple concepts such as the 2D transformations (translation,
rotation, etc.) will necessarily be encoded as 'Actions'. We go on to create a
Transform class that can capture one series of Actions. Both Actions and Transforms
involve a single output for an input. The Generator class can combine multiple
Transforms, as well as repetition of these transforms, to generate larger objects
such as lines, rectangles, and tilings.
"""
import re
from typing import TYPE_CHECKING, Any

from arc.actions import Action, Actions
from arc.types import ArgsList, Position
from arc.util import logger

if TYPE_CHECKING:
    from arc.object import Object

# This regex parses the series of actions represented in a Generator 'code'.
# It expects a series of alphabet characters each optionally followed by
# a comma-delimited set of signed integers. These correspond to an Action and
# any associated arguments to the call. The trailing, optional 'copies'
# (represented by an asterisk and positive integer) is handled by the
# 'copies_regex' below, which indicates repeated application of the Actions.
act_regex = re.compile(r"([a-zA-Z])(-?\d*(?:,-?\d+)*)")
copies_regex = re.compile(r"\*(\d+)")

log = logger.fancy_logger("Transform", level=30)


class TransformError(Exception):
    pass


class Transform:
    def __init__(
        self,
        actions: list[type[Action]],
        args: ArgsList | None = None,
    ):
        self.actions = actions
        self.args: ArgsList = args or [tuple([])] * len(self.actions)
        if len(self.args) < len(self.actions):
            log.error(f"Insufficient arguments for Transform: {args} -> {actions}")
            raise TransformError

    def __bool__(self) -> bool:
        return len(self.actions) > 0

    def __len__(self) -> int:
        return len(self.actions)

    def __str__(self) -> str:
        if not self:
            return "ID()"

        output = ", ".join(
            [
                f"{act}({','.join(map(str, args))})"
                for act, args in zip(self.actions, self.args)
            ]
        )
        return output

    @property
    def char(self) -> str:
        """Characteristic of the Transform: the unique, sorted Action keys involved."""
        characteristic: set[str] = set()
        for action in self.actions:
            characteristic.add(action.code)
        return "".join(sorted(characteristic))

    @classmethod
    def from_code(cls, code: str) -> "Transform":
        """Create a Transform from a code (string of Action keys and args)."""
        chars, raw_args = zip(*act_regex.findall(code))
        args: ArgsList = [
            tuple(map(int, item.split(","))) if item else tuple() for item in raw_args
        ]
        return cls(
            actions=[Actions.map[char] for char in chars],
            args=args,
        )

    @property
    def code(self) -> str:
        """Return the string of action keys and args."""
        msg = ""
        for action, args in zip(self.actions, self.args):
            msg += f"{action.code}{','.join(map(str, args))}"
        return msg

    @property
    def props(self) -> int:
        """The number of properties used in defining the Transform."""
        action_ct = len(self.actions)
        arg_ct = sum([len(args) for args in self.args])
        return action_ct + arg_ct

    def concat(self, other: "Transform") -> "Transform":
        """Combine two transforms together."""
        return Transform(
            actions=self.actions.copy() + other.actions.copy(),
            args=self.args.copy() + other.args.copy(),
        )

    def copy(self, **kwargs: Any) -> "Transform":
        """Create a copy of the Transform, modifying any properties by keyword."""
        return Transform(
            actions=self.actions.copy(),
            args=self.args.copy(),
            **kwargs,
        )

    def apply(self, object: "Object", default_args: Position = (0, 0)) -> "Object":
        """Creates a new object based on the set of actions and arguments."""
        result = object
        for action, args in zip(self.actions, self.args):
            try:
                result = action.act(result, *args)
            except:
                result = action.act(result, *default_args)
        return result
