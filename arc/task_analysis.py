"""The ARC tasks are drawn from a broad domain, which includes many concepts
such 2D transformations, symmetry, relational logic, kinematics, and others.
If we break down the body of tasks by labelling them with certain 'traits',
we can divide and conquer the problem.
"""

from arc.task import Task

## Progress on training tasks
all_solved = {
    8,
    10,
    16,
    17,
    28,
    # 30,
    31,
    36,
    39,
    49,
    53,
    57,
    61,
    83,
    87,
    100,
    106,
    116,
    128,
    140,
    142,
    150,
    152,
    155,
    164,
    179,
    188,
    194,
    210,
    241,
    249,
    # 254,
    263,
    276,
    287,
    305,
    373,
    374,
    380,
}

## Progress on evaluation tasks
all_eval_solved = {17, 49, 78, 177, 179, 197, 217, 301, 309, 312, 366, 372}

# Large tilings tend to take a while, keep them separate
large_tiling = {17, 61, 287, 305}

fast_solved = all_solved - large_tiling

# Tasks from the DreamCoder work, symmetry-based
dc_idxs = {83, 87, 106, 116, 140, 142, 150, 152, 155, 172, 179, 210, 211, 241} | {
    249,
    311,
    380,
}

# Tasks from the Minimum Description Length work
# These tend to be more static in structure across cases
mdl_idxs = (
    {10, 28, 31, 36, 47, 53, 100, 111, 128, 129, 153, 156, 171, 174, 192}
    | {222, 245, 253, 254, 261, 263, 267, 276, 290, 293, 294, 298, 299}
    | {300, 354, 362, 373, 374}
)

# Set of tasks that engage in significant compute at present, and are not
# under consideration for finding a solution. We filter these out to
# save time on larger runs.
blocklist = {
    54,
    74,
    77,
    80,
    110,
    118,
    162,
    165,
    175,
    205,
    208,
    243,
    255,
    265,
    303,
}


class TaskTraits:
    methods: list[str] = [
        "color_ct",
        "const_size",
        "size",
        "solved",
        "tiled",
        "from_paper",
    ]

    @classmethod
    def color_ct(cls, task: Task) -> None:
        colors = [0] * 10
        for scene in task.cases:
            for color, _ in scene.input.rep.c_rank:
                colors[color] = 1
            for color, _ in scene.output.rep.c_rank:
                colors[color] = 1
        label = sum(colors)
        if label > 5:
            label = "many"
        task.traits.add(f"{label}-color")

    @classmethod
    def const_size(cls, task: Task) -> None:
        if all(
            [scene.input.rep.shape == scene.output.rep.shape for scene in task.cases]
        ):
            task.traits.add("constant_size")

    @classmethod
    def size(cls, task: Task) -> None:
        small, large = 36, 225  # e.g. 6x6 and 15x15
        if all([scene.input.rep.size <= small for scene in task.cases]) and all(
            [scene.output.rep.size <= small for scene in task.cases]
        ):
            task.traits.add("small")
        elif all([scene.input.rep.size >= large for scene in task.cases]) or all(
            [scene.output.rep.size >= large for scene in task.cases]
        ):
            task.traits.add("large")

    @classmethod
    def tiled(cls, task: Task) -> None:
        threshold = 0.95
        # Test if either all inputs or outputs have high ordering
        ordered = False
        for scene in task.cases:
            rows, row_order = scene.input.rep.order_trans_row
            cols, col_order = scene.input.rep.order_trans_col
            if rows == 1 and cols == 1:
                continue
            elif row_order < threshold and col_order < threshold:
                ordered = False
                break
            else:
                ordered = True
        if ordered:
            task.traits.add("tiled")
            return

        for scene in task.cases:
            rows, row_order = scene.output.rep.order_trans_row
            cols, col_order = scene.output.rep.order_trans_col
            if rows == 1 and cols == 1:
                continue
            elif row_order < threshold and col_order < threshold:
                ordered = False
                break
            else:
                ordered = True

        if ordered:
            task.traits.add("tiled")
        return

    @classmethod
    def solved(cls, task: Task) -> None:
        if task.idx in all_solved:
            task.traits.add("solved")

    @classmethod
    def from_paper(cls, task: Task) -> None:
        if task.idx in mdl_idxs:
            task.traits.add("mdl")

        if task.idx in dc_idxs:
            task.traits.add("dreamcoder")
