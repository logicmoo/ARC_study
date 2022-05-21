from typing import Any

from arc.definitions import Constants as cst
from arc.comparisons import ObjectComparison, default_comparisons
from arc.generator import Transform
from arc.object import Object
from arc.types import ObjectPath
from arc.util import logger


log = logger.fancy_logger("ObjectDelta", level=30)


class ObjectDelta:
    """Determine the 'difference' between two objects.

    This class analyzes how many transformations and properties it requires to
    turn the 'left' object into the 'right'. It calculates an integer measure called
    'distance', as well as the series of standard transformations to apply.
    """

    def __init__(
        self,
        left: Object,
        right: Object,
        tag: int = 0,
        path: ObjectPath = tuple(),
        comparisons: list["ObjectComparison"] = default_comparisons,
    ):
        self.left: Object = left
        self.right: Object = right
        self.tag: int = tag
        self.path: ObjectPath = path
        self.null: bool = False
        self.transform: Transform = Transform([])
        self.comparisons = comparisons
        if left == right:
            return

        log.debug("Comparing:")
        log.debug(f"  {left}")
        log.debug(f"  {right}")
        for comparison in comparisons:
            transform = comparison(self.left, self.right)
            self.transform = self.transform.concat(transform)
        log.debug(f"->{self.transform}")

        if self.transform.apply(left) != right:
            self.null = True
            log.debug("Failed test")

    def __bool__(self) -> bool:
        return not self.null

    @property
    def dist(self) -> int:
        """Returns the 'transformation distance' metric between objects.

        The transformation distance is the total number of parameters required to
        transform the 'left' object to the 'right'. This is equal to the sum of the
        number of Actions plus the sum of the total number of additional arguments
        supplied to the Actions.
        """
        if self.null:
            return cst.MAX_DIST

        return self.transform.props

    @property
    def actions(self) -> set[Any]:
        """Returns the set of Actions used in the transformation"""
        return set([act for act in self.transform.actions])

    @property
    def _name(self):
        return f"Delta({self.dist}): {self.transform}"

    def __repr__(self) -> str:
        return f"{self._name}: {self.left.id} -> {self.right.id}"

    def __lt__(self, other: "ObjectDelta") -> bool:
        return self.dist < other.dist

    def diff(self, other: "ObjectDelta") -> int:
        """Returns a similarity measure between ObjectDeltas."""
        return len(self.actions & other.actions)
