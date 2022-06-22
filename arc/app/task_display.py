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
            st.write("No solution found")

        filename: str = f"task{task_idx}_solution.html"
        if not os.path.isfile(filename):
            plot_solution(solution, filename=filename, width=1000, height=1000)

        with open(filename, "r", encoding="utf-8") as fh:
            pyvis_html = fh.read()
            components.html(pyvis_html, width=500, height=500)

    # Decomposition
    with st.expander(f"Decomposition of Scene {scene_idx}", expanded=True):
        left, right = st.columns(2)  # type: ignore
        with left:
            st.image(cached_plot((task_idx, int(scene_idx), "input")))  # type: ignore
        with right:
            st.image(cached_plot((task_idx, int(scene_idx), "output")))  # type: ignore

    # linking
    with st.expander(f"Linking between the Scene's input and output", expanded=True):
        st.image(cached_plot((task_idx, int(scene_idx))))  # type: ignore

    # Solution
    with st.expander(f"The Solution parameters", expanded=True):
        sol = _arc[task_idx].solution
        st.write(f"Common structure of outputs:")  # type: ignore
        md_lines: list[str] = []
        for line in sol.template._display_node(tuple([])):
            indent = len(line) - len(line.lstrip())
            if indent > 0:
                md_lines.append(line[:indent] + "* " + line[indent:])
            else:
                md_lines.append(line)
        st.markdown("\n".join(md_lines))  # type: ignore
