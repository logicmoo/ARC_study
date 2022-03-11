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
from typing import TYPE_CHECKING, Any

from arc.actions import Action

if TYPE_CHECKING:
    from arc.object import Object


# This regex parses the series of actions represented in a Generator 'code'
# It expects a series of alphabet characters each optionally followed by
# a comma-delimited set of signed integers. The trailing, optional 'count'
# (represented by an asterisk and positive integer) is handled by the
# 'count_regex' below.
act_regex = re.compile(r"([a-zA-Z])(-?\d*(?:,-?\d+)*)")
count_regex = re.compile(r"\*(\d+)")

# TODO Seems cleaner to move 'count' to a 'copies'(?) param on Generator
# leaving Transform as a non-generative means to mutate objects. This will
# probably be important for handling Scene input->output
class Transform:
    def __init__(
        self,
        actions: list[Any],
        args: list[tuple[int, ...]] | None = None,
        count: int = 1,
    ):
        self.actions = actions
        self.args = args or [tuple()] * len(self.actions)
        if len(self.args) < len(self.actions):
            self.args.extend([tuple()] * (len(self.actions) - len(self.args)))
        self.count = count

    def __str__(self) -> str:
        output = ", ".join(
            [f"{act.__name__}{args}" for act, args in zip(self.actions, self.args)]
        )
        if self.count != 1:
            output += f" x{self.count}"
        return output

    @property
    def code(self) -> str:
        msg = ""
        for action, args in zip(self.actions, self.args):
            msg += f"{Action().rev_map[action.__name__]}{','.join(map(str, args))}"

        if self.count != 1:
            msg += f"*{self.count}"
        return msg

    @property
    def props(self) -> int:
        count_ct = 1 if self.count != 1 else 0
        action_ct = len(self.actions)
        arg_ct = sum([len(args) for args in self.args])
        return action_ct + arg_ct + count_ct

    def spawn(self, **kwargs) -> "Transform":
        return Transform(
            actions=self.actions.copy(),
            args=self.args.copy(),
            count=self.count,
            **kwargs,
        )

    def apply(self, object: "Object") -> list["Object"]:
        """Creates a new object based on the set of actions, applied count times."""
        results = [object.spawn()]
        current = object
        for i in range(self.count):
            for action, args in zip(self.actions, self.args):
                current = action(current, *args)
            results.append(current)
        return results


class Generator:
    def __init__(self, transforms: list[Transform], bound=None):
        self.transforms = transforms
        self.bound = bound

    def __str__(self) -> str:
        trans_str = ",".join([str(tr) for tr in self.transforms])
        return f"({trans_str})"

    @property
    def codes(self) -> list[str]:
        return [trans.code for trans in self.transforms]

    @classmethod
    def from_codes(cls, codes: list[str], bound: tuple[int, int] | None = None):
        transforms = []
        for code in codes:
            chars, raw_args = zip(*act_regex.findall(code))
            count = 1
            if search_obj := count_regex.search(code):
                count = int(search_obj.groups()[0])
            actions = [Action()[char] for char in chars]
            args = [
                tuple(map(int, item.split(","))) if item else tuple()
                for item in raw_args
            ]
            transforms.append(Transform(actions, args, count))
        return cls(transforms=transforms, bound=bound)

    def materialize(self, object: "Object") -> list["Object"]:
        """Creates a normalized (no generators) object hierarchy."""
        results = [object.spawn()]
        for transform in self.transforms:
            new_results = []
            for current in results:
                new_results.extend(transform.apply(current))
            results = new_results
        return results

    @property
    def dim(self) -> int:
        return len(self.transforms)

    @property
    def props(self) -> int:
        return sum([trans.props for trans in self.transforms])
