import os

import streamlit as st
import streamlit.components.v1 as components
from arc.app.util import cached_plot
from arc.viz import plot_solution


def task_display(task_idx: int):
    st.title("Solution")  # type: ignore
    st.caption("Showing the stages of determining a solution")  # type: ignore

    _arc = st.session_state.arc

    scene_options = list(range(len(_arc[task_idx].cases)))
    scene_idx = st.sidebar.selectbox("Choose scene", scene_options, index=0)  # type: ignore

    with st.expander(f"Visual overview of Task {task_idx}", expanded=True):
        st.image(cached_plot(task_idx))  # type: ignore

    # Solution
    with st.expander(f"Solution", expanded=True):
        solution = _arc[task_idx].solution
        if not solution:
            st.write("No solution found")  # type: ignore

        filename: str = f"task{task_idx}_solution.html"
        if not os.path.isfile(filename):
            plot_solution(solution, filename=filename)

        with open(filename, "r", encoding="utf-8") as fh:
            components.html(fh.read(), width=1400, height=700)  # type: ignore

    # Decomposition
    with st.expander(f"Decomposition of Scene {scene_idx}", expanded=True):
        left, right = st.columns(2)  # type: ignore
        with left:
            st.image(cached_plot((task_idx, int(scene_idx), "input")))  # type: ignore
        with right:
            st.image(cached_plot((task_idx, int(scene_idx), "output")))  # type: ignore

    # Linking
    with st.expander(f"Linking between the Scene's input and output", expanded=True):
        st.image(cached_plot((task_idx, int(scene_idx))))  # type: ignore
