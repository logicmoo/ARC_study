import dataclasses


@dataclasses.dataclass
class Settings:
    N: int = 400
    folder: str = "data/training"
    default_pickle_id: str = "demo_run"
    grid_width: int = 10


# Annotations
class Notes:
    explorer = """
**_The ARC dataset is a collection of visual tasks that
are expressed through simple grids using only a handful of colors.
Each task contains 2 or more input/output pairs of grids which demonstrate
some abstract process. I term these grid pairs Scenes. The challenge is to
learn from the demonstration Scenes and create the correct output grid for
a test input._**

**_There are 800 tasks in the public dataset, split evenly into training and
evaluation sets. You can explore the 400 training tasks here, and see how
my approach handles each task. The sidebar can be used to filter the tasks by
some convenient measures. By default, the filter is set to "solved" showing tasks
that are known to generate a valid solution, which are probably the more interesting
cases up front._**

**_The code is open-sourced on [GitHub](https://github.com/dereklarson/ARC_study)_**
"""

    decomposition = """
**_Each scene is decomposed into a representation that minimizes the
number of parameters used, loosely following Minimum Description Length.
This is done across the scene: jointly between the input and output. Thus,
if a complex shape is recognized across both grids, this reduces the
overall length of representation._**

**_This representation is a hierarchy of Objects. Each Object specifies
a 3-tuple (row, column, color), and has child Objects which
inherit the parent's traits. One simple way to reduce description length is
collect points of a like color into one group. Also, an Object may specify a
repeated transformation, e.g. a vertical line can be specified by repeating a 
vertical translation by one unit. This allows lines, rectangles, 
tilings, etc. efficient representations._**

**_Broadly, one can look at this process as "adding internal structure"
to the pixel representation of the grids. One starts with a single
"root" Object containing every "pixel" Object. The goal is then to add
middle layers that take advantage of patterns to compress the
description. The images below show this hierarchy in a row-wise fashion._**
"""

    linking = """
**_Once the input and output representations are determined, one
can search for the minimally specified "path" that recreates the output
given the input. Given high-quality representations, there are usually
only a few Objects of interest, and one can quickly check every pair
of input and output Objects for similarity and whether there exists
a short transformation path between them. At this stage, the code mostly
looks for single-transform links._**
"""

    solution = """
**_Finally, a Solution is the full specification of how to convert an input grid to an
output grid. The decomposition stage is handled by simply defining the "characteristic"
of the expected decomposition: the unique set of decomposition processes to use. The
core of the Solution is defining a directed graph of transformations that can take the
compressed input representation and create the output._**

**_I identify a set of 3 fundamental 'vertex types' that can be
flexibly composed to generate diagrams with a wide range of functionality:_**
- **Selection**: Choose some Objects from a set of Objects based on criteria
- **Variable**: Derive an integer value from a set of Objects
- **Transform**: mutate an Object via Actions (e.g. Translate, Recolor)
"""
