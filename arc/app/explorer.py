import matplotlib.pyplot as plt
import streamlit as st
from arc.app.settings import Notes, Settings
from arc.app.util import cached_plot


def explorer():
    st.title("ARC Explorer")  # type: ignore
    st.caption("Displaying the input grid of the first Scene for each Task")  # type: ignore

    if not st.session_state.hide_annotations:
        st.markdown(Notes.explorer)  # type: ignore

    _arc = st.session_state.arc
    tasks: list[int] = list(sorted(_arc.selection))
    grid: list[list[int]] = [[] for _ in range(Settings.grid_width)]
    for idx, task_idx in enumerate(tasks):
        grid[idx % Settings.grid_width].append(task_idx)

    # TODO Storing page_idx in session state didn't give permanence
    columns = st.columns(Settings.grid_width)  # type: ignore
    for column, task_idxs in zip(columns, grid):  # type: ignore
        with column:
            for task_idx in filter(None, task_idxs):

                def on_click(_idx: int):
                    def action():
                        st.session_state.task_idx = _idx

                    return action

                st.button(str(task_idx), on_click=on_click(task_idx))
                try:
                    with open(f"thumbnails/task{task_idx:0>3}.png", "rb") as fh:
                        st.image(plt.imread(fh))  # type: ignore
                except FileNotFoundError:
                    st.image(cached_plot((task_idx, 0, "input"), "raw"))  # type: ignore
