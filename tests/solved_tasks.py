import argparse
from arc.arc import ARC

# TODO Task 30 needs Align action touched up
solved_tasks = {8, 16, 39, 188, 194, 309}

# Large tilings tend to take a while, keep them separate
large_tiling = {17, 61, 287, 305}

# Tasks from the DreamCoder work, symmetry-based
dc_solved = {83, 87, 106, 140, 142, 150, 152, 155, 179, 380}

# Tasks from the Minimum Description Length work
# These tend to be more static in structure across cases
mdl_solved = {10, 31, 36, 53, 263, 276, 374}

fast_solved = solved_tasks | dc_solved | mdl_solved
all_solved = fast_solved | large_tiling

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the fastest solved tasks (~6s)")
    parser.add_argument(
        "-a", "--all", help="Run all solved tasks (~20s)", action="store_true"
    )
    args = parser.parse_args()

    tasks_to_run = fast_solved
    if args.all:
        tasks_to_run = all_solved

    _arc = ARC(idxs=tasks_to_run)
    _arc.set_log({"Task": 30, "Scene": 30})
    _arc.solve_tasks(quiet=True)
    for task_idx in tasks_to_run:
        assert "Solved" in _arc[task_idx].traits
