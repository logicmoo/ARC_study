from queue import Queue
from collections import defaultdict

def find_shapes(pattern=[], ignored_colors=[0], nrange=1):
    """ Uses breadth first search BFS to find vertically and horizontally joined
    cells, each grouping of cells is classified as a shape.
    >>> find_shapes([[0, 1, 0, 0, 1],[1, 1, 0, 1, 1]],[0])
    [[(0, 1, 1), (1, 1, 1), (1, 0, 1)], [(0, 4, 1), (1, 4, 1), (1, 3, 1)]]

    >>> find_shapes([[0, 3, 0, 0, 5],[1, 1, 0, 1, 1]],[0])
    [[(0, 1, 3), (1, 1, 1), (1, 0, 1)], [(0, 4, 5), (1, 4, 1), (1, 3, 1)]]
    """

    y_size = len(pattern)
    x_size = len(pattern[0])

    shapes = []
    visited = []

    for y, yrow in enumerate(pattern):
        for x, color in enumerate(yrow):
            cell = (y, x, color)

            # if not visited yet
            if cell in visited:
                continue

            # if cell is not ignored
            if color in ignored_colors:
                continue

            # create a queue for a new shape
            queue = Queue()

            # put the cell in the shape - it will
            # act as the starting point
            queue.put(cell)

            # list for cells of a single shape
            shape = []
            while not queue.empty():

                # current cell
                c = queue.get()

                # see if it was already visited
                if c in visited:
                    continue
                else:
                    visited.append(c)

                yy, xx, col = c
                if col in ignored_colors:
                    continue

                # It's part of the shape, append.
                # All cells from the queue are a part
                # of the same shape
                shape.append(c)

                # horizontal and vertical neighbours from
                # current cell in range of nrange
                neighbours = list(range(-nrange, nrange+1))
                neighbours.remove(0)
                for i in neighbours:

                    # add neighbours to the queue
                    if 0 <= yy + i < y_size:
                        queue.put((yy + i, xx, pattern[yy + i][xx]))

                    if 0 <= xx + i < x_size:
                        queue.put((yy, xx + i, pattern[yy][xx + i]))

            shapes.append(shape)
    return shapes


#
def group_by_color(shape):
    """ This takes a shape (a collection of points) [(y, x, color)...]
    and groups them by color each color will have its own list
    >>> group_by_color([(0, 1, 4), (3, 5, 4), (9, 3, 1), (12, 19, 1)])
    [[(0, 1, 4), (3, 5, 4)], [(9, 3, 1), (12, 19, 1)]]
    """

    # a default dictionary with lists
    grouped_by_color = defaultdict(list)

    # iterate over shape
    for cell in shape:
        y, x, color = cell

        # add cells of the same color to the same list
        # in the dictionary
        grouped_by_color[color].append((y, x, color))

    # return all lists from the dictionary
    return [grouped_by_color[colr] for colr in grouped_by_color]


# this function takes a list
def find_colors(shapes):
    """ Takes a list of shapes with cells (y, x, color) and finds their common and uncommon colors.
    >>> find_colors([[(0, 1, 4), (3, 5, 4), (9, 3, 1)], [(4, 11, 3), (5, 1, 3), (12, 19, 1)]])
    ([1], [[4], [3]])

    >>> find_colors([[(0, 1, 4), (3, 5, 8), (9, 3, 1)], [(4, 11, 3), (5, 1, 8), (12, 19, 1), (3, 1, 7)]])
    ([8, 1], [[4], [3, 7]])
    """

    # collect all colors for all shapes
    # where each shape has a set of colors
    shapes_colors_sets = []
    for shape in shapes:
        colors = set()
        for cell in shape:
            y, x, color = cell
            colors.add(color)

        shapes_colors_sets.append(colors)

    # intersect between all sets of all shapes
    common = shapes_colors_sets[0]
    for shape_colors in shapes_colors_sets:
        common = common.intersection(shape_colors)

    # Difference between each set and common
    uncommon = []
    for shape_colors in shapes_colors_sets:
        uncommon.append(list(shape_colors - common))

    return list(common), uncommon


def get_of_color(shape, target_colors):
    """ From shape gets cells of color
    >>> get_of_color([(0, 1, 2), (1, 1, 2), (3, 3, 5), (9, 1, 5), (5, 1, 8)], [2])
    [(0, 1, 2), (1, 1, 2)]

    >>> get_of_color([(0, 1, 2), (1, 1, 2), (3, 3, 5), (9, 1, 5), (5, 1, 8)], [2, 5])
    [(0, 1, 2), (1, 1, 2), (3, 3, 5), (9, 1, 5)]

    >>> get_of_color([(0, 1, 2), (1, 1, 2), (3, 3, 5), (9, 1, 5), (5, 1, 8)], [5, 8])
    [(3, 3, 5), (9, 1, 5), (5, 1, 8)]
    """

    out = []
    for cell in shape:
        y, x, color = cell

        if color in target_colors:
            out.append(cell)

    return out


def redraw_in_scale(shape, scale):
    """ Redraws a shape in a different scale
    >>> redraw_in_scale([(0, 0, 5), (0, 1, 9)], 2)
    [(0, 0, 5), (0, 1, 5), (1, 0, 5), (1, 1, 5), (0, 2, 9), (0, 3, 9), (1, 2, 9), (1, 3, 9)]
    """

    temp_new_shape = []

    # For simplicity first rescale Ys
    anchor_y, _, _ = min(shape, key=lambda c: c[0])  # anchor for Y - used for progressive scaling
    for cell in shape:
        y, x, color = cell

        for s in range(scale):
            new_y = y + (scale - 1) * (y - anchor_y) + s  # rescale algorithm
            temp_new_shape.append((new_y, x, color))

    new_shape = []

    # Then rescale Xs
    _, anchor_x, _ = min(temp_new_shape, key=lambda c: c[1])  # anchor for X - used for progressive scaling
    for cell in temp_new_shape:
        y, x, color = cell

        for s in range(scale):
            new_x = x + (scale - 1) * (x - anchor_x) + s  # rescale algorithm
            new_shape.append((y, new_x, color))

    return new_shape


def recolor(shape, source_colors, target_color):
    """ Recolors a shape from source_color to target_color
    >>> recolor([(0, 0, 1), (0, 1, 1), (0, 2, 1), (0, 3, 5)], [1], 4)
    [(0, 0, 4), (0, 1, 4), (0, 2, 4), (0, 3, 5)]

    >>> recolor([(0, 0, 1), (0, 1, 1), (0, 2, 2), (0, 3, 5)], [1, 2], 4)
    [(0, 0, 4), (0, 1, 4), (0, 2, 4), (0, 3, 5)]
    """

    new_shape = []
    for cell in shape:
        y, x, color = cell

        if color in source_colors:
            color = target_color

        new_shape.append((y, x, color))

    return new_shape


# does not consider rotation
def position_matching_by_color(source_shape, target_shape, color):
    """ Matched source_shape position with target_shape by color.
    >>> position_matching_by_color([(0, 0, 1), (3, 3, 2)], [(6, 7, 2), (9, 2, 1), (3, 6, 8)], 2)
    [(3, 4, 1), (6, 7, 2)]
    """

    common_cells_target = list(filter(lambda c: c[2] == color, target_shape))
    common_cells_source = list(filter(lambda c: c[2] == color, source_shape))

    target_min = min(common_cells_target, key=lambda c: c[0] + c[1])
    source_min = min(common_cells_source, key=lambda c: c[0] + c[1])

    y_offset = target_min[0] - source_min[0]
    x_offset = target_min[1] - source_min[1]

    new_shape = []
    for cell in source_shape:
        y, x, color = cell
        new_shape.append((y + y_offset, x + x_offset, color))

    return new_shape


def draw_on_pattern(shape, pattern):
    """Draws a shape on a pattern
    >>> draw_on_pattern([(0, 0, 1), (0, 1, 3), (1, 1, 8)], [[0, 0, 0], [0, 0, 0]])
    [[1, 3, 0], [0, 8, 0]]
    """

    y_size = len(pattern)
    x_size = len(pattern[0])
    new_pattern = pattern.copy()

    for cell in shape:
        y, x, color = cell

        if 0 <= y < y_size and 0 <= x < x_size:
            new_pattern[y][x] = color

    return new_pattern


if __name__ == "__main__":
    import doctest

    doctest.testmod()
