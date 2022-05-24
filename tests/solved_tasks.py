import argparse
from arc.arc import ARC
from arc.task_analysis import fast_solved, all_solved

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
    _arc.set_log({"Task": 30, "Scene": 30, "Template": 40})
    _arc.solve_tasks(quiet=True)
    for task_idx in tasks_to_run:
        assert "Solved" in _arc[task_idx].traits
