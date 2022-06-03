"""A simple script to initiate debugging runs."""

from arc.arc import ARC

task_idx = 128
_arc = ARC(idxs={task_idx})
_arc.set_log(10)
_arc[task_idx].solve()
