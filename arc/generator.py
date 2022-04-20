"""The Transform and Generator classes handle mutations of objects.

On its own, the Object class can only represent hierarchical collections of points.
Intuitively, however, primitives such as rectangles shouldn't be represented as their
constituent points, but a higher-level abstraction requiring fewer specifying 
parameters. We also want to avoid enumerating these primitives as much as possible,
favoring a more generalized approach. Thus, the Generator class.

We assume that the simple concepts such as the 2D transformations (translation,
rotation, etc.) will necessarily be encoded as 'Actions'. We go on to create a
Transform class that can capture one series of Actions. Both Actions and Transforms
involve a single output for an input. The Generator class can combine multiple
Transforms, as well as repetition of these transforms, to generate larger objects
such as lines, rectangles, and tilings.
"""
import re
from typing import TYPE_CHECKING, Any, Callable, TypeAlias

from arc.actions import Action
from arc.types import Position


if TYPE_CHECKING:
    from arc.object import Object

ActionType: TypeAlias = Callable[..., "Object"]

# This regex parses the series of actions represented in a Generator 'code'.
# It expects a series of alphabet characters each optionally followed by
# a comma-delimited set of signed integers. These correspond to an Action and
# any associated arguments to the call. The trailing, optional 'copies'
# (represented by an asterisk and positive integer) is handled by the
# 'copies_regex' below, which indicates repeated application of the Actions.
act_regex = re.compile(r"([a-zA-Z])(-?\d*(?:,-?\d+)*)")
copies_regex = re.compile(r"\*(\d+)")


class Transform:
    def __init__(
        self,
        actions: list[ActionType],
        args: list[tuple[int, ...]] | None = None,
    ):
        self.actions = actions
        self.args = args or [tuple()] * len(self.actions)
        if len(self.args) < len(self.actions):
            self.args.extend([tuple()] * (len(self.actions) - len(self.args)))

    def __str__(self) -> str:
        if not self.actions:
            return "ID()"

        output = ", ".join(
            [f"{act.__name__}{args}" for act, args in zip(self.actions, self.args)]
        )
        return output

    @property
    def char(self) -> str:
        """Characteristic of the Transform: the unique, sorted Action keys involved."""
        characteristic: set[str] = set()
        for action in self.actions:
            characteristic.add(Action().rev_map[action.__name__])
        return "".join(sorted(characteristic))

    @classmethod
    def from_code(cls, code: str) -> "Transform":
        """Create a Transform from a code (string of Action keys and args)."""
        chars, raw_args = zip(*act_regex.findall(code))
        args = [
            tuple(map(int, item.split(","))) if item else tuple() for item in raw_args
        ]
        return cls(
            actions=[Action()[char] for char in chars],
            args=args,
        )

    @property
    def code(self) -> str:
        """Return the string of action keys and args."""
        msg = ""
        for action, args in zip(self.actions, self.args):
            msg += f"{Action().rev_map[action.__name__]}{','.join(map(str, args))}"
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
            # TODO WIP Inspection of Action args seems necessary soon.
            try:
                result = action(result, *args)
            except:
                result = action(result, *default_args)
        return result


class Generator:
    """Generate a more complex object by repeated application of Transforms.

    A generator is a means to more compactly represent ordered shapes. For example,
    a blue horizontal line of length 8 could be represented by 8 points in a row:
        [Object(0, 0, 1), Object(0, 1, 1), ... , Object(0, 7, 1)]
    or, we can use a generator with a horizontal translation as it's transform
    repeated 7 times, which uses fewer properties to define.

    By default, an Object with a generator will use as its 'seed' a Dot defined by
    the Object's anchor (row, col, color), which is superceded if the Object has any
    children.

    To create a red/blue checkerboard, we can define the following:
        Object(children = [Object(0, 0, 1), Object(0, 1, 2),
                           Object(1, 0, 2), Object(1, 1, 1)],
               generator = Generator.from_codes(["R1*3", "C1*3"])
    which is a 2x2 grid evenly tiled 3 extra times along both axes.
    """

    def __init__(
        self,
        transforms: list[Transform],
        copies: list[int] = [],
        bound: tuple[int, int] | None = None,
    ):
        self.transforms = transforms
        self.copies = copies or [0] * len(self.transforms)
        self.bound = bound

    def __str__(self) -> str:
        msg: list[str] = []
        for trans, copies in zip(self.transforms, self.copies):
            curr = trans.code
            if copies is not None:
                curr += f"*{copies}"
            msg.append(curr)
        return f"({','.join(msg)})"

    @property
    def codes(self) -> list[str]:
        codes: list[str] = []
        for trans, copies in zip(self.transforms, self.copies):
            curr = trans.code
            if copies:
                curr += f"*{copies}"
            codes.append(curr)
        return codes

    @classmethod
    def from_codes(cls, codes: list[str], bound: tuple[int, int] | None = None):
        transforms: list[Transform] = []
        arg_copies: list[int] = []
        for code in codes:
            copies = 0
            if search_obj := copies_regex.search(code):
                copies = int(search_obj.groups()[0])
            transforms.append(Transform.from_code(code))
            arg_copies.append(copies)
        return cls(transforms=transforms, copies=arg_copies, bound=bound)

    @property
    def char(self) -> str:
        """Characteristic of the Generator: the unique, sorted Actions involved."""
        characteristic: set[str] = set()
        for transform in self.transforms:
            characteristic |= set(transform.char)
        return "".join(sorted(characteristic))

    @property
    def dim(self) -> int:
        return len(self.transforms)

    @property
    def props(self) -> int:
        copies_props = sum([1 if val != 0 else 0 for val in self.copies])
        return sum([trans.props for trans in self.transforms]) + copies_props

    def copy(self, **kwargs: Any) -> "Generator":
        new_args = {
            "transforms": [trans.copy() for trans in self.transforms],
            "copies": self.copies.copy(),
        }
        new_args.update(kwargs)
        return Generator(**new_args)  # type: ignore

    def materialize(self, object: "Object") -> list["Object"]:
        """Creates a materialized (no generators) object hierarchy."""
        results = [object.copy()]
        for transform, copies in zip(self.transforms, self.copies):
            new_results: list[Object] = []
            for current in results:
                if copies:
                    new_results.append(current)
                    for _ in range(copies):
                        current = transform.apply(current, object.shape)
                        new_results.append(current)
                else:
                    new_results.append(transform.apply(current))
            results = new_results
        return results
