import os

import numpy as np

from arc.arc import ARC


def test_pickling() -> None:
    test_pid = ".arc_test"
    arc = ARC(N=5)
    arc.dump(pid=test_pid)
    loaded = ARC.load(pid=test_pid)
    os.remove(f"{test_pid}.pkl")
    # Note: This test is fairly superficial, only ensuring bulk operation
    # Check every input grid matches up in before and after
    for task_idx in arc.tasks:
        for scene_idx, scene in enumerate(arc.tasks[task_idx].cases):
            load_grid = loaded[task_idx].cases[scene_idx].input.rep.grid
            assert np.array_equal(scene.input.rep.grid, load_grid)


def test_selection() -> None:
    arc = ARC(N=5)
    arc[1].traits.add("small")
    arc[2].traits.add("small")
    arc[4].traits.add("small")
    arc.blacklist = {4}

    arc.select(selection={1, 3, 5})
    assert arc.selection == {1, 3, 5}

    arc.select(selector={"small"})
    assert arc.selection == {1, 2}

    arc.select(selection={1, 3}, selector={"small"})
    assert arc.selection == {1}
