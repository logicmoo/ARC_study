"""Define custom types used throughout the codebase."""
from typing import Any, Literal, TypeAlias, TypedDict

import numpy as np

# For the input data, we have a 3-type hierarchy
BoardData: TypeAlias = list[list[int]]


class SceneData(TypedDict):
    input: BoardData
    output: BoardData


class TaskData(TypedDict):
    train: list[SceneData]
    test: list[SceneData]


Grid: TypeAlias = np.ndarray[Any, np.dtype[np.int64]]  # type: ignore
Shape: TypeAlias = tuple[int, int]

Args: TypeAlias = tuple[int, ...]
ArgsList: TypeAlias = list[tuple[int, ...]]


Position: TypeAlias = tuple[int, int]
PositionList: TypeAlias = list[Position]
PositionSet: TypeAlias = set[Position]
Point: TypeAlias = tuple[int, int, int]
PointList: TypeAlias = list[Point]
PointSet: TypeAlias = set[Point]
PointDict: TypeAlias = dict[Position, int]

Property: TypeAlias = Literal["row", "col", "color", "row_bound", "col_bound"]

BaseObjectPath: TypeAlias = tuple[int, ...]
PropertyPath: TypeAlias = str
