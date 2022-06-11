import streamlit as st
from arc.app.util import cached_plot
from arc.processes import process_map


def solution(task_idx: int):
    st.title("Solution")  # type: ignore
    st.caption("Showing the stages of determining a solution")  # type: ignore

    _arc = st.session_state.arc

    scene_options = list(range(len(_arc[task_idx].cases)))
    scene_idx = st.sidebar.selectbox("Choose scene", scene_options, index=0)  # type: ignore

    with st.expander(f"Visual overview of Task {task_idx}", expanded=True):
        st.image(cached_plot(task_idx))  # type: ignore

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
        actions = ", ".join([str(process_map[code]) for code in sol.characteristic])
        st.write(f"Decomposition characteristic: {sol.characteristic} | {actions}")  # type: ignore
        st.write(f"Attention at depth: {sol.level_attention}")  # type: ignore
        st.write(f"Nodes in the Solution graph:")  # type: ignore
        for node in sol.nodes:
            st.write(node)  # type: ignore
        st.write(f"Common structure of outputs:")  # type: ignore
        md_lines: list[str] = []
        for line in sol.template._display_node(tuple([])):
            indent = len(line) - len(line.lstrip())
            if indent > 0:
                md_lines.append(line[:indent] + "* " + line[indent:])
            else:
                md_lines.append(line)
        st.markdown("\n".join(md_lines))  # type: ignore
