import numpy as np
import streamlit as st

from arc.app.settings import Settings
from arc.app.util import cached_plot


def explorer():
    _arc = st.session_state.arc
    pages: dict[int, list[list[int]]] = {}
    tasks = list(sorted(_arc.selection))
    H, W = Settings.grid_height, Settings.grid_width
    page_size = H * W
    for p_idx in range(len(tasks) // page_size + 1):
        base_idx = p_idx * page_size
        page = np.array(tasks[base_idx : base_idx + page_size])
        page.resize(page_size)
        pages[p_idx] = page.reshape((W, H), order="F").tolist()

    title_col, slider_col, _ = st.columns([3, 1, 1])
    with title_col:
        st.title(f"Explore each input to the first scene")
    page_idx = 1
    if len(pages) > 1:
        with slider_col:
            page_idx = st.select_slider(
                label="Page", options=[i + 1 for i in range(len(pages))]
            )

    # TODO Storing page_idx in session state didn't give permanence
    # grid = pages[int(st.session_state.page_idx)]
    grid = pages[page_idx - 1]
    columns = st.columns(W)
    for column, task_idxs in zip(columns, grid):
        with column:
            for task_idx in filter(None, task_idxs):

                def on_click(_idx: int):
                    def action():
                        st.session_state.task_idx = _idx

                    return action

                st.button(str(task_idx), on_click=on_click(task_idx))
                st.image(cached_plot((task_idx, 0, "input"), "Input"))
