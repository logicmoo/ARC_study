import os
import time

import streamlit as st
import streamlit.components.v1 as components
from arc.app.settings import Notes
from arc.app.util import cached_plot
from arc.viz import plot_solution


def task_display(task_idx: int):
    st.title(f"Task {task_idx}")  # type: ignore

    with st.expander(f"Visual overview of Task {task_idx}", expanded=True):
        st.image(cached_plot(task_idx))  # type: ignore

    # Solution
    st.title("Solution")  # type: ignore
    st.caption("Showing the three stages of determining a solution")  # type: ignore

    ## Find solution
    container = st.empty()  # type: ignore
    container.markdown("_Solving Task..._")  # type: ignore
    start = time.time()
    _arc = st.session_state.arc
    if not _arc[task_idx].fail and not _arc[task_idx].solution:
        _arc[task_idx].run()
    seconds = round(time.time() - start, 2)
    container.markdown(f"_Spent {seconds}s on solution_")  # type: ignore

    scene_options = list(range(len(_arc[task_idx].cases)))
    scene_idx = st.sidebar.selectbox("Choose scene", scene_options, index=0)  # type: ignore
    scene = _arc[task_idx][scene_idx]

    # Decomposition
    with st.expander(f"Decomposition of Scene {scene_idx}", expanded=True):
        if not st.session_state.hide_annotations:
            st.subheader("Decomposition")  # type: ignore
            st.markdown(Notes.decomposition)  # type: ignore

        raw_ct = scene.input.raw.props + scene.output.raw.props
        compression = round(raw_ct / scene.props, 1)
        st.write(f"Raw properties: {raw_ct}")  # type: ignore
        st.write(f"Representation parameters: {scene.props}")  # type: ignore
        st.write(f"Compression ratio: {compression}")  # type: ignore

        left, right = st.columns(2)  # type: ignore
        with left:
            st.image(cached_plot((task_idx, int(scene_idx), "input"), None, False))  # type: ignore
        with right:
            st.image(cached_plot((task_idx, int(scene_idx), "output"), None, False))  # type: ignore

    # Linking
    with st.expander(f"Linking Scene {scene_idx}", expanded=True):
        if not st.session_state.hide_annotations:
            st.subheader("Linking")  # type: ignore
            st.markdown(Notes.linking)  # type: ignore

        st.write(f"Distance between input and output: {scene.dist}")  # type: ignore
        st.image(cached_plot((task_idx, int(scene_idx)), None, False))  # type: ignore

    with st.expander("Solution", expanded=True):
        if not st.session_state.hide_annotations:
            st.subheader("Solution")  # type: ignore
            st.markdown(Notes.solution)  # type: ignore

        solution = _arc[task_idx].solution
        if not solution:
            st.write("No solution found")  # type: ignore
        else:
            st.write(f"Total properties in solution: {_arc[task_idx].solution.props}")  # type: ignore

        filename: str = f"task{task_idx}_solution.html"
        if not os.path.isfile(filename):
            plot_solution(solution, filename=filename)

        with open(filename, "r", encoding="utf-8") as fh:
            components.html(fh.read(), width=1400, height=700)  # type: ignore
