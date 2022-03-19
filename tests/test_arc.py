import os

import numpy as np
import pytest

from arc.arc import ARC, FailedSolve


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
    arc.scan()
    arc.blacklist = {4}

    arc.select(selection={1, 3, 5})
    assert arc.selection == {1, 3, 5}

    arc.select(selector={"constant_size"})
    assert arc.selection == {2, 5}

    arc.select(selection={2, 4}, selector={"constant_size"})
    assert arc.selection == {2}


def test_complete_run() -> None:
    # TODO Double-check this
    # arc = ARC(idxs={1})
    # with pytest.raises(FailedSolve):
    #     arc.solve_tasks()

    arc = ARC(idxs={10})
    arc.solve_tasks()
