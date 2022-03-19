"""The Transform and Generator classes handle mutations of objects.

On its own, the Object class can only represent hierarchical collections of points.
Intuitively, however, primitives such as rectangles shouldn't be represented as their
constituent points, but a higher-level abstraction requiring fewer specifying 
parameters. We also want to avoid enumerating these primitives as much as possible,
favoring a more generalized approach. Thus, the Generator class.

We assume that the simple concepts such as the 2D transformations (translation,
rotation, etc.) will necessarily be encoded as 'Actions'. We go on to create a
Transform class that can capture one series of Actions. Then, the more
universal Generator class is defined as a series of transforms.
"""
import re
from typing import TYPE_CHECKING, Any, Callable, TypeAlias

from arc.actions import Action


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
        output = ", ".join(
            [f"{act.__name__}{args}" for act, args in zip(self.actions, self.args)]
        )
        return output

    @property
    def char(self) -> str:
        """Characteristic of the Transform: the unique, sorted Actions involved."""
        characteristic = set()
        for action in self.actions:
            characteristic.add(Action().rev_map[action.__name__])
        return "".join(sorted(characteristic))

    @property
    def code(self) -> str:
        msg = ""
        for action, args in zip(self.actions, self.args):
            msg += f"{Action().rev_map[action.__name__]}{','.join(map(str, args))}"
        return msg

    @property
    def props(self) -> int:
        action_ct = len(self.actions)
        arg_ct = sum([len(args) for args in self.args])
        return action_ct + arg_ct

    def spawn(self, **kwargs) -> "Transform":
        return Transform(
            actions=self.actions.copy(),
            args=self.args.copy(),
            **kwargs,
        )

    def apply(self, object: "Object") -> "Object":
        """Creates a new object based on the set of actions and arguments."""
        result = object
        for action, args in zip(self.actions, self.args):
            result = action(result, *args)
        return result


class Generator:
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
        msg = []
        for trans, copies in zip(self.transforms, self.copies):
            curr = str(trans)
            if copies is not None:
                curr += f"*{copies}"
            msg.append(curr)
        return f"({','.join(msg)})"

    @property
    def codes(self) -> list[str]:
        codes = []
        for trans, copies in zip(self.transforms, self.copies):
            curr = trans.code
            if copies:
                curr += f"*{copies}"
            codes.append(curr)
        return codes

    @classmethod
    def from_codes(cls, codes: list[str], bound: tuple[int, int] | None = None):
        transforms = []
        arg_copies = []
        for code in codes:
            chars, raw_args = zip(*act_regex.findall(code))
            copies = None
            if search_obj := copies_regex.search(code):
                copies = int(search_obj.groups()[0])
            actions = [Action()[char] for char in chars]
            args = [
                tuple(map(int, item.split(","))) if item else tuple()
                for item in raw_args
            ]
            transforms.append(Transform(actions, args))
            arg_copies.append(copies)
        return cls(transforms=transforms, copies=arg_copies, bound=bound)

    @property
    def char(self) -> str:
        """Characteristic of the Generator: the unique, sorted Actions involved."""
        characteristic = set()
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

    def spawn(self, **kwargs) -> "Generator":
        new_args = {
            "transforms": [trans.spawn() for trans in self.transforms],
            "copies": self.copies.copy(),
        }
        new_args.update(kwargs)
        return Generator(**new_args)

    def materialize(self, object: "Object") -> list["Object"]:
        """Creates a normalized (no generators) object hierarchy."""
        results = [object.spawn()]
        for transform, copies in zip(self.transforms, self.copies):
            new_results = []
            for current in results:
                if copies:
                    new_results.append(current)
                    for i in range(copies):
                        current = transform.apply(current)
                        new_results.append(current)
                else:
                    new_results.append(transform.apply(current))
            results = new_results
        return results
