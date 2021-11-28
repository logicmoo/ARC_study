#!/usr/bin/python

# Student ID: 17436176
# Student name: Jaroslaw Janas
# Repository: https://github.com/jaroslawjanas/ARC

import os, sys
import json
import numpy as np
import re
from math import sqrt
from colorama import Fore, Style, init
init() # this colorama init helps Windows 

from utilities import find_shapes, group_by_colour, find_colours, \
    redraw_in_scale, recolour, position_matching_by_colour, draw_on_pattern, get_of_colour

# Note this repo was rebased with upstream
# that's why all commits are withing minutes of each other

# I will go over commonalities at the end of each solve_*

# For this task take the following steps:
#   1. Split the pattern into shapes with black as ignored colour
#   2. Find out which shape is the source pattern
#       - this can be done bu checking if length of colours matches,
#           since the target shapes always have only two starting squares
#           in two different colours, the source shape does not
#   3. Determine scale for each of target shapes.
#       - square root of a single color of target
#   4. Rescale the source shape to target's scale
#   5. Recolor the rescale-source-shape to match target's colours
#   6. Using the common colours re-position, no need to worry about rotation

def solve_57aa92db(pattern):
    # Pattern separation using BFS
    shapes = find_shapes(pattern=pattern, ignored_colours=[0], nrange=1)

    shapes_by_colours = []
    for shape in shapes:
        shapes_by_colours.append(group_by_colour(shape))

    # The shape with unequal number of colours is the source
    # Also the length of a side of the odd colour is the scale
    source_shape_index = None
    scales = [None] * len(shapes_by_colours)

    # Figuring out the index of source shape and scales of other shapes
    for i, shape_by_colours in enumerate(shapes_by_colours):
        group_size = len(shape_by_colours[0])

        for colour_group in shape_by_colours:
            l = len(colour_group)

            if l != group_size:
                if l < group_size:
                    group_size = l
                    source_shape_index = i

        scales[i] = int(sqrt(group_size))

    source_shape = shapes[source_shape_index]
    [common_colour], uncommon_colours = find_colours(shapes)

    # Final transformation
    new_pattern = pattern.copy()
    for idx, (shape, scale) in enumerate(zip(shapes, scales)):

        # Skip is source shape
        if shape == source_shape:
            continue

        # If different scales don't rescale
        if scales[source_shape_index] != scale:
            new_shape = redraw_in_scale(source_shape, scale)
        else:
            new_shape = source_shape

        # Recolour to match target's colour
        re_coloured_new_shape = recolour(new_shape, [uncommon_colours[source_shape_index][0]], uncommon_colours[idx][0])

        # Position the newly rescaled-recoloured shape to match the target's position
        positioned_new_shape = position_matching_by_colour(re_coloured_new_shape, shape, common_colour)

        # Draw on new_pattern
        new_pattern = draw_on_pattern(positioned_new_shape, new_pattern)

    return new_pattern
# Everything solved correctly.

# There are no similarities at this stage but as I worked on this task
# I developed a lot of useful functions that are located in utilities.py
# The next tasks are specifically chosen to make the best out of the already
# developed utilities and minimize additional workload.


# This task requires the following steps:
#   1. Using BFS algorithm find_shapes find all shapes with blue and black cells
#   2. Filter out cells with only black cells
#   3. Fill all cells in the remaining shape with blue

def solve_9edfc990(pattern):
    # Identify colours of interest
    all_colours = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
    colours_of_interest = {0, 1}  # black and blue
    ignored_colours = list(all_colours - colours_of_interest) # set other colours as ignored

    # Find all shapes with black and blue cells
    shapes = find_shapes(pattern=pattern, ignored_colours=ignored_colours, nrange=1)

    # Filter out shapes that only have black cells
    new_shapes = []
    for shape in shapes:
        # if no blue, remove
        if len(get_of_colour(shape, [1])) < 1:
            continue

        new_shapes.append(shape)
    shapes = new_shapes

    # Recolour all black cells to blue
    new_shapes = []
    for shape in shapes:
        new_shapes.append(recolour(shape, [0], 1))

    # Construct a new pattern
    new_pattern = pattern.copy()
    for shape in new_shapes:
        new_pattern = draw_on_pattern(shape, new_pattern)

    return new_pattern
# Everything solved correctly.

# As you can see I ended up re-using a lot of functions, the main one being find_shapes.
# Being able to separate constructs in a pattern, based on its structure makes the problem much simpler.
# Split and conquer!
# Because my underlying structure of shapes is consistent I can reuse functions such as recolour or draw_on_pattern.
# I developed get_of_colour while forking on the first problem but never ended up using it.
# It was quite useful in this task.


# This task requires the following steps:
#   1. Find out the colour of the border.
#   2. Find the shapes. Use nrange=2 so that the algorithm can go over the border.
#       - use nrange=2 so that the algorithm can go over the border.
#       - ignore border colour and background colour (black)
#   3. Determine the source shape
#       - all shapes in scale so simply get the biggest one
#   4. Find out what the common colours between shapes are
#   5. Reposition a new source shape onto the target using the common colours as reference

def solve_39e1d7f9(pattern):
    # Find a solid row = border colour
    border_colour = None
    for y, yrow in enumerate(pattern):
        if np.all(yrow == yrow[0]):  # if has the same element (border)
            border_colour = yrow[0]

    # Find shapes using BFS algorithm, note nrange=2
    shapes = find_shapes(pattern=pattern, ignored_colours=[0, border_colour], nrange=2)

    # Find the common_colours
    [common_colour], uncommon_colours = find_colours(shapes)

    # Find the source shape - since all are in the same scale, get the biggest
    source_shape = max(shapes, key=lambda s: len(s))

    new_pattern = pattern.copy()
    for shape in shapes:
        # Position the new source shape
        positioned_new_shape = position_matching_by_colour(source_shape, shape, common_colour)

        # Draw
        new_pattern = draw_on_pattern(positioned_new_shape, new_pattern)

    return new_pattern
# Everything solved correctly.

# You can see a lot of similarities. Once again I used find_shapes and other utilites that I developed
# such as find_colours, position_matching_by_colour and draw_on_pattern.
# A lot of these tasks require moving shapes and determining their colours.
# The big picture might be different but the underlying small operation/transformations are often the same.
# It's only a matter of ordering them properly.

# Overall a lot of commonalities came from recolouring, repositioning and finding out common and uncommon colours.
# I also ended up using find_shapes function in each single task, which made my life so much easier.

# In utilities I used two python libraries, queue and defaultdict.
# I mostly used queue in find_shapes - based on BFS that's why.
# Defaultdict was useful when dealing with colours, we don't know what colours are present
# in a pattern so can't properly initialize a dictionary with lists. Technically speaking I could
# but then I would have to check for empty lists which would be ugly and more complex.

def main():
    # Find all the functions defined in this file whose names are
    # like solve_abcd1234(), and run them.

    # regex to match solve_* functions and extract task IDs
    p = r"solve_([a-f0-9]{8})"
    tasks_solvers = []
    # globals() gives a dict containing all global names (variables
    # and functions), as name: value pairs.
    for name in globals():
        m = re.match(p, name)
        if m:
            # if the name fits the pattern eg solve_abcd1234
            ID = m.group(1)  # just the task ID
            solve_fn = globals()[name]  # the fn itself
            tasks_solvers.append((ID, solve_fn))

    for ID, solve_fn in tasks_solvers:
        # for each task, read the data and call test()
        directory = os.path.join("..", "data", "training")
        json_filename = os.path.join(directory, ID + ".json")
        data = read_ARC_JSON(json_filename)
        test(ID, solve_fn, data)


# ref https://stackoverflow.com/a/54955094
# Enum-like class of different styles
# these are the styles for background
class style():
    BLACK = '\033[40m'
    RED = '\033[101m'
    GREEN = '\033[42m'
    YELLOW = '\033[103m'
    BLUE = '\033[44m'
    MAGENTA = '\033[45m'
    CYAN = '\033[46m'
    WHITE = '\033[47m'
    RESET = '\033[0m'
    DARKYELLOW = '\033[43m'
    DARKRED = '\033[41m'
    # DARKYELLOW = '\033[2m' + '\033[33m'
    # DARKRED = '\033[2m' + '\033[31m'
    # DARKWHITE = '\033[2m' + '\033[37m'
    
# the order of colours used in ARC
# (notice DARKYELLOW is just an approximation)
cmap = [style.BLACK,
       style.BLUE,
       style.RED,
       style.GREEN,
       style.YELLOW,
       style.WHITE,
       style.MAGENTA,
       style.DARKYELLOW,
       style.CYAN,
       style.DARKRED]


def echo_colour(x):
    s = " " # print a space with a coloured background

    for row in x:
        for i in row:
            # print a character twice as grids are too "thin" otherwise
            print(cmap[int(i)] + s + s + style.RESET, end="")
        print("")

    
## TODO write a more convenient diff function, either for grids
## or for json files (because each task is stored as a single line
## of json in GitHub).

    
def read_ARC_JSON(filepath):
    """Given a filepath, read in the ARC task data which is in JSON
    format. Extract the train/test input/output pairs of
    grids. Convert each grid to np.array and return train_input,
    train_output, test_input, test_output."""

    # Open the JSON file and load it
    data = json.load(open(filepath))

    # Extract the train/test input/output grids. Each grid will be a
    # list of lists of ints. We convert to Numpy.
    train_input = [np.array(data['train'][i]['input']) for i in range(len(data['train']))]
    train_output = [np.array(data['train'][i]['output']) for i in range(len(data['train']))]
    test_input = [np.array(data['test'][i]['input']) for i in range(len(data['test']))]
    test_output = [np.array(data['test'][i]['output']) for i in range(len(data['test']))]

    return (train_input, train_output, test_input, test_output)


def test(taskID, solve, data):
    """Given a task ID, call the given solve() function on every
    example in the task data."""
    print(taskID)
    train_input, train_output, test_input, test_output = data
    print("Training grids")
    for x, y in zip(train_input, train_output):
        yhat = solve(x)
        show_result(x, y, yhat)
    print("Test grids")
    for x, y in zip(test_input, test_output):
        yhat = solve(x)
        show_result(x, y, yhat)


def show_result(x, y, yhat):
    print("Input")
    echo_colour(x) # if echo_colour(x) doesn't work, uncomment print(x) instead
    #print(x)
    print("Correct output")
    echo_colour(y)
    #print(y)
    print("Our output")
    echo_colour(yhat)
    #print(yhat)
    print("Correct?")
    if y.shape != yhat.shape:
        print(f"False. Incorrect shape: {y.shape} v {yhat.shape}")
    else:
        print(np.all(y == yhat))


if __name__ == "__main__": main()

