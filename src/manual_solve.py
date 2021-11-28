#!/usr/bin/python

import os, sys
import json
import numpy as np
import re
from math import sqrt
from utilities import find_shapes, group_by_color, find_colors, redraw_in_scale, recolor, position_matching_by_color, draw_on_pattern

from colorama import Fore, Style, init
init() # this colorama init helps Windows 


    

### YOUR CODE HERE: write at least three functions which solve
### specific tasks by transforming the input x and returning the
### result. Name them according to the task ID as in the three
### examples below. Delete the three examples. The tasks you choose
### must be in the data/training directory, not data/evaluation.

def solve_57aa92db(pattern):

    # pattern separation using BFS
    shapes = find_shapes(pattern)

    shapes_by_colors = []
    for shape in shapes:
        shapes_by_colors.append(group_by_color(shape))

    # The shape with unequal number of colors is the source
    # Also the length of a side of the odd color is the scale
    source_shape_index = None
    scales = [None] * len(shapes_by_colors)

    for i, shape_by_colors in enumerate(shapes_by_colors):
        group_size = len(shape_by_colors[0])

        for color_group in shape_by_colors:
            l = len(color_group)

            if l != group_size:
                if l < group_size:
                    group_size = l
                    source_shape_index = i

        scales[i] = int(sqrt(group_size))

    source_shape = shapes[source_shape_index]
    [common_color], uncommon_colors = find_colors(shapes)

    new_pattern = pattern.copy()
    for idx, (shape, scale) in enumerate(zip(shapes, scales)):

        if shape == source_shape:
            continue

        if scales[source_shape_index] != scale:
            new_shape = redraw_in_scale(source_shape, scale)
        else:
            new_shape = source_shape

        re_colored_new_shape = recolor(new_shape, [uncommon_colors[source_shape_index][0]], uncommon_colors[idx][0])

        positioned_new_shape = position_matching_by_color(re_colored_new_shape, shape, common_color)

        new_pattern = draw_on_pattern(positioned_new_shape, new_pattern)

    return new_pattern

    


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
            ID = m.group(1) # just the task ID
            solve_fn = globals()[name] # the fn itself
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

