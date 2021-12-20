"""Define custom types used throughout the codebase."""
from typing import TypeAlias, TypedDict

# For the input data, we have a 3-type hierarchy
BoardData: TypeAlias = list[list[int]]


class SceneData(TypedDict):
    input: BoardData
    output: BoardData


class TaskData(TypedDict):
    train: list[SceneData]
    test: list[SceneData]


Position: TypeAlias = tuple[int, int]
PositionList: TypeAlias = list[Position]
PositionSet: TypeAlias = set[Position]
Point: TypeAlias = tuple[int, int, int]
PointList: TypeAlias = list[Point]
PointSet: TypeAlias = set[Point]
PointDict: TypeAlias = dict[Position, int]
