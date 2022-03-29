"""The ARC tasks are drawn from a broad domain, which includes many concepts
such 2D transformations, symmetry, relational logic, kinematics, and others.
If we break down the body of tasks by labelling them with certain 'traits',
we can divide and conquer the problem.
"""

from arc.task import Task


class TaskTraits:
    methods: list[str] = ["color_ct", "const_size", "size", "tiled"]

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
            R, C, order = scene.input.rep.order
            if R == 1 and C == 1:
                continue
            elif order < threshold:
                ordered = False
                break
            else:
                ordered = True
        if ordered:
            task.traits.add("tiled")
            return

        for scene in task.cases:
            rows, cols, order = scene.output.rep.order
            if rows == 1 and cols == 1:
                continue
            elif order < threshold:
                ordered = False
                break
            else:
                ordered = True

        if ordered:
            task.traits.add("tiled")
        return
