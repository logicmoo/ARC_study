import re
from typing import TYPE_CHECKING, Any

from arc.actions import Action

if TYPE_CHECKING:
    from arc.object import Object


act_regex = re.compile(r"([A-Za-z]+)(\d*)")


class Transform:
    def __init__(self, actions: list[Any], count: int = 1):
        self.actions = actions
        self.count = count

    def __str__(self) -> str:
        act_str = ", ".join([act.__name__ for act in self.actions])
        return f"({act_str}x{self.count})"

    def spawn(self, **kwargs) -> "Transform":
        return Transform(actions=self.actions, count=self.count, **kwargs)

    def apply(self, object: "Object") -> list["Object"]:
        """Creates a new object based on the set of actions, applied count times."""
        results = [object.spawn()]
        current = object
        for i in range(self.count):
            for action in self.actions:
                current = action(current)
            results.append(current)
        return results


class Generator:
    def __init__(self, transforms: list[Transform], bound=None):
        self.transforms = transforms
        self.bound = bound

    def __str__(self) -> str:
        trans_str = ",".join([str(tr) for tr in self.transforms])
        return f"({trans_str})"

    @classmethod
    def from_codes(cls, codes: list[str], bound: tuple[int, int] = None):
        transforms = []
        for code in codes:
            chars, count = re.match(act_regex, code).groups()  # type: ignore
            actions = [Action()[char] for char in chars]
            transforms.append(Transform(actions, int(count)))
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
        return len(self.transforms) * 2
