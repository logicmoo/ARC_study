from arc.arc import ARC

# TODO Task 30 needs Selection fixing (negation or props)
# TODO Task 31 has some decomposition issues
solved_tasks = {8, 16, 17, 39}

dc_solved = {87, 140, 142, 150, 152, 155, 179, 380}
mdl_solved = {10, 374}

solved_tasks |= dc_solved
solved_tasks |= mdl_solved

_arc = ARC(idxs=solved_tasks)
_arc.set_log({"Task": 30, "Scene": 30})
_arc.solve_tasks(quiet=True)
for task_idx in solved_tasks:
    assert "Solved" in _arc[task_idx].traits
