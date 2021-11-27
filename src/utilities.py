from queue import Queue
from collections import defaultdict

# This uses BFS (Breath first search)
def find_shapes(pattern):
    position_of_colored = Queue()

    for x, xrow in enumerate(pattern):
        for y, cell in enumerate(xrow):
            # if cell is not black
            if cell != 0:
                # add to the queue
                position_of_colored.put((x, y))

    # list for multiple shapes [ [shape1], [shape2] ]
    shapes = []
    visited = []

    # while there are colored cells in the queue
    while not position_of_colored.empty():
        # get the cell
        cell = position_of_colored.get()

        # see if it was visited already
        if cell in visited:
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

            # see if it was visited already
            if c in visited:
                continue
            else:
                visited.append(c)

            x, y = c
            # It's part of the shape, append
            # all cells from the queue are a part
            # of the same shape
            shape.append(c)

            # horizontal and vertical cells from
            # current cell
            for i in [-1, 1]:

                # if neighbours are not black
                # add them to the queue
                # we add cells from the queue
                # to the shape in line 51
                if pattern[x + i][y] != 0:
                    queue.put((x + i, y))
                    # print(f"({x}, {y}) has neighbours")

                if pattern[x][y + i] != 0:
                    queue.put((x, y + i))
                    # print(f"({x}, {y}) has neighbours")

        shapes.append(shape)
    return shapes

def group_by_color(shape, pattern):
    # a default dictionary with lists
    grouped_by_color = defaultdict(list)

    # iterate over shape
    for cell in shape:
        x, y = cell
        cell_color = pattern[x][y]

        # add cells of the same color to the same list
        # in the dictionary
        grouped_by_color[cell_color].append((x, y))

    # return all lists from the dictionarySS
    return [grouped_by_color[color] for color in grouped_by_color]
