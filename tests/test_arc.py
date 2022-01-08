import os

import numpy as np

from arc.arc import ARC


def test_pickling() -> None:
    test_idxs = {8, 10, 16, 30}
    test_pid = ".arc_test"
    arc = ARC(idxs=test_idxs)
    arc.dump(pid=test_pid)
    loaded = ARC.load(pid=test_pid)
    os.remove(f"{test_pid}.pkl")
    # Note: This test is fairly superficial, only ensuring bulk operation
    # Check every input grid matches up in before and after
    for task_idx in arc.tasks:
        for scene_idx, scene in enumerate(arc.tasks[task_idx].cases):
            load_grid = loaded[task_idx].cases[scene_idx].input.rep.grid
            assert np.array_equal(scene.input.rep.grid, load_grid)
