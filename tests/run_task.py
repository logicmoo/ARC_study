from arc.arc import ARC

task_idx = 30
_arc = ARC(idxs={task_idx})
_arc[task_idx].solve()
