from queue import Queue
from collections import defaultdict


def find_shapes(pattern=[], ignored_colours=[0], nrange=1):
    """ Uses breadth first search (BFS) to find vertically and horizontally joined
    cells, each grouping of cells is classified as a shape.

    The nrange argument determines how many vertical horizontal cells
    are considered as neighbours, nrange=2 will consider cells
        (x-2), (x-1), (x+1), (x+2), (y-2), (y-1), (y+1), (y+2) as neighbours.

    Ignored colours argument tells the algorithm which colours should not be considered
    as shapes or part of them.

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
        for x, colour in enumerate(yrow):
            cell = (y, x, colour)

            # if not visited yet
            if cell in visited:
                continue

            # if cell is not ignored
            if colour in ignored_colours:
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
                if col in ignored_colours:
                    continue

                # It's part of the shape, append.
                # All cells from the queue are a part
                # of the same shape
                shape.append(c)

                # horizontal and vertical neighbours from
                # current cell in range of nrange
                neighbours = list(range(-nrange, nrange + 1))
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
def group_by_colour(shape):
    """ This takes a shape (a collection of points) [(y, x, colour),...]
    and groups them by colour. Each colour will have its own list.

    >>> group_by_colour([(0, 1, 4), (3, 5, 4), (9, 3, 1), (12, 19, 1)])
    [[(0, 1, 4), (3, 5, 4)], [(9, 3, 1), (12, 19, 1)]]
    """

    # a default dictionary with lists
    grouped_by_colour = defaultdict(list)

    # iterate over shape
    for cell in shape:
        y, x, colour = cell

        # add cells of the same colour to the same list
        # in the dictionary
        grouped_by_colour[colour].append((y, x, colour))

    # return all lists from the dictionary
    return [grouped_by_colour[colr] for colr in grouped_by_colour]


# this function takes a list
def find_colours(shapes):
    """ Takes a list of shapes with cells (y, x, colour) and finds their common and uncommon colours.
    Note that uncommon colours are a nested list, where each nested list corresponds to uncommon colours
    of a particular shape - different shapes could have different uncommon colours.

    >>> find_colours([[(0, 1, 4), (3, 5, 4), (9, 3, 1)], [(4, 11, 3), (5, 1, 3), (12, 19, 1)]])
    ([1], [[4], [3]])

    >>> find_colours([[(0, 1, 4), (3, 5, 8), (9, 3, 1)], [(4, 11, 3), (5, 1, 8), (12, 19, 1), (3, 1, 7)]])
    ([8, 1], [[4], [3, 7]])
    """

    # collect all colours for all shapes
    # where each shape has a set of colours
    shapes_colours_sets = []
    for shape in shapes:
        colours = set()
        for cell in shape:
            y, x, colour = cell
            colours.add(colour)

        shapes_colours_sets.append(colours)

    # intersect between all sets of all shapes
    common = shapes_colours_sets[0]
    for shape_colours in shapes_colours_sets:
        common = common.intersection(shape_colours)

    # Difference between each set and common
    uncommon = []
    for shape_colours in shapes_colours_sets:
        uncommon.append(list(shape_colours - common))

    return list(common), uncommon


def get_of_colour(shape, target_colours):
    """ From a shape gets cells of colour.

    >>> get_of_colour([(0, 1, 2), (1, 1, 2), (3, 3, 5), (9, 1, 5), (5, 1, 8)], [2])
    [(0, 1, 2), (1, 1, 2)]

    >>> get_of_colour([(0, 1, 2), (1, 1, 2), (3, 3, 5), (9, 1, 5), (5, 1, 8)], [2, 5])
    [(0, 1, 2), (1, 1, 2), (3, 3, 5), (9, 1, 5)]

    >>> get_of_colour([(0, 1, 2), (1, 1, 2), (3, 3, 5), (9, 1, 5), (5, 1, 8)], [5, 8])
    [(3, 3, 5), (9, 1, 5), (5, 1, 8)]
    """

    out = []
    for cell in shape:
        y, x, colour = cell

        if colour in target_colours:
            out.append(cell)

    return out


def redraw_in_scale(shape, scale):
    """ Takes a shape and redraws it in a different bigger scale.
    The positions are offseted but the colors are preserved.

    For simplicity the algorithm first rescales Ys then Xs.
    Each rescale uses anchor to calculate the position of new/old cells.
    The further away we are from the anchor the bigger the offset needs to be
    since we already added (scale-1) number of extra cells up to that point.

    The algorithm is new_pos = pos + (scale-1) * (pos - anchor) + 0:scale

    >>> redraw_in_scale([(0, 0, 5), (0, 1, 9)], 2)
    [(0, 0, 5), (0, 1, 5), (1, 0, 5), (1, 1, 5), (0, 2, 9), (0, 3, 9), (1, 2, 9), (1, 3, 9)]
    """

    temp_new_shape = []

    # For simplicity first rescale Ys
    anchor_y, _, _ = min(shape, key=lambda c: c[0])  # anchor for Y - used for progressive scaling
    for cell in shape:
        y, x, colour = cell

        for s in range(scale):
            new_y = y + (scale - 1) * (y - anchor_y) + s  # rescale algorithm
            temp_new_shape.append((new_y, x, colour))

    new_shape = []

    # Then rescale Xs
    _, anchor_x, _ = min(temp_new_shape, key=lambda c: c[1])  # anchor for X - used for progressive scaling
    for cell in temp_new_shape:
        y, x, colour = cell

        for s in range(scale):
            new_x = x + (scale - 1) * (x - anchor_x) + s  # rescale algorithm
            new_shape.append((y, new_x, colour))

    return new_shape


def recolour(shape, source_colours, target_colour):
    """ Recolours a shape from source_colours to target_colour.

    >>> recolour([(0, 0, 1), (0, 1, 1), (0, 2, 1), (0, 3, 5)], [1], 4)
    [(0, 0, 4), (0, 1, 4), (0, 2, 4), (0, 3, 5)]

    >>> recolour([(0, 0, 1), (0, 1, 1), (0, 2, 2), (0, 3, 5)], [1, 2], 4)
    [(0, 0, 4), (0, 1, 4), (0, 2, 4), (0, 3, 5)]
    """

    new_shape = []
    for cell in shape:
        y, x, colour = cell

        if colour in source_colours:
            colour = target_colour

        new_shape.append((y, x, colour))

    return new_shape


# does not consider rotation
def position_matching_by_colour(source_shape, target_shape, colour):
    """ Calculates offset using the min position values of the
    matching colours of source and target shape.
    Then offsets source accordingly. Rotation is not considered.
    No after shifting checks are done.

    >>> position_matching_by_colour([(0, 0, 1), (3, 3, 2)], [(6, 7, 2), (9, 2, 1), (3, 6, 8)], 2)
    [(3, 4, 1), (6, 7, 2)]
    """

    # filter out uncommon coloured cells, only keep the commonly coloured ones
    common_cells_target = list(filter(lambda c: c[2] == colour, target_shape))
    common_cells_source = list(filter(lambda c: c[2] == colour, source_shape))

    # get min position of commonly coloured cells for both shapes
    target_min = min(common_cells_target, key=lambda c: c[0] + c[1])
    source_min = min(common_cells_source, key=lambda c: c[0] + c[1])

    # calculate offsets
    y_offset = target_min[0] - source_min[0]
    x_offset = target_min[1] - source_min[1]

    # shift source according to the offest
    new_shape = []
    for cell in source_shape:
        y, x, colour = cell
        new_shape.append((y + y_offset, x + x_offset, colour))

    return new_shape


def draw_on_pattern(shape, pattern):
    """ Draws a shape on a pattern.

    >>> draw_on_pattern([(0, 0, 1), (0, 1, 3), (1, 1, 8)], [[0, 0, 0], [0, 0, 0]])
    [[1, 3, 0], [0, 8, 0]]
    """

    y_size = len(pattern)
    x_size = len(pattern[0])
    new_pattern = pattern.copy()

    for cell in shape:
        y, x, colour = cell

        if 0 <= y < y_size and 0 <= x < x_size:
            new_pattern[y][x] = colour

    return new_pattern


if __name__ == "__main__":
    import doctest

    doctest.testmod()
