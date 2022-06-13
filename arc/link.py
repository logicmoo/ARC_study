from abc import ABC, abstractmethod

from arc.definitions import Constants as cst
from arc.object import Object
from arc.transform import Transform
from arc.types import BaseObjectPath
from arc.util import logger

log = logger.fancy_logger("Link", level=30)


class Link(ABC):
    def __init__(self, left: Object, right: Object, base: BaseObjectPath) -> None:
        self.left = left
        self.right = right
        self.base = base

    @property
    @abstractmethod
    def dist(self) -> int:
        """Returns the 'transformation distance' metric between objects.

        This will depend on the type of link.
        """
        return 0

    def __lt__(self, other: "Link") -> bool:
        return self.dist < other.dist

    @property
    @abstractmethod
    def _header(self) -> str:
        return ""

    def __repr__(self) -> str:
        return f"{self._header} | {self.left.id} -> {self.right.id} @ {self.base}"


class VariableLink(Link):
    def __init__(
        self,
        left: Object,
        right: Object,
        base: BaseObjectPath,
        property: str,
        value: int,
    ) -> None:
        super().__init__(left, right, base)
        self.property = property
        self.value = value

    @property
    def dist(self) -> int:
        return 2

    @property
    def _header(self):
        return f"Var({self.dist}): {self.property}"


class ObjectDelta(Link):
    """Determine the 'difference' between two objects.

    This class analyzes how many transformations and properties it requires to
    turn the 'left' object into the 'right'. It calculates an integer measure called
    'distance', as well as the series of standard transformations to apply.
    """

    def __init__(
        self,
        left: Object,
        right: Object,
        transform: Transform,
        base: BaseObjectPath = tuple(),
        tag: int = 0,
        null: bool = False,
    ):
        super().__init__(left, right, base)
        self.tag: int = tag
        self.transform: Transform = transform
        self.null: bool = null

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
    def _header(self):
        return f"Delta({self.dist}): {self.transform}"
