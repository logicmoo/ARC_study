from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from arc.object import Object


def chebyshev_vector(left: "Object", right: "Object") -> tuple[int, int]:
    left_min_row, left_min_col = left.loc
    left_max_row = left.row + left.shape[0]
    left_max_col = left.col + left.shape[1]

    right_min_row, right_min_col = right.loc
    right_max_row = right.row + right.shape[0]
    right_max_col = right.col + right.shape[1]

    dist: list[int | None] = [None, None]
    # Check for any horizontal overlap
    if left_min_row >= right_max_row:
        dist[0] = right_max_row - left_min_row
    elif left_max_row <= right_min_row:
        dist[0] = right_min_row - left_max_row
    # Check for any vertical overlap
    if left_min_col >= right_max_col:
        dist[1] = right_max_col - left_min_col
    elif left_max_col <= right_min_col:
        dist[1] = right_min_col - left_max_col

    if dist[0] is None:
        if dist[1] is None:
            return (0, 0)
        else:
            return (0, dist[1])
    elif dist[1] is None:
        return (dist[0], 0)
    else:
        if abs(dist[0]) < abs(dist[1]):
            return (dist[0], 0)
        else:
            return (0, dist[1])
