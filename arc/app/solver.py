import streamlit as st

from arc.app.util import cached_plot


def solver(task_idx: int):
    _arc = st.session_state.arc

    scene_options = list(range(len(_arc[task_idx].cases)))
    scene_idx = st.sidebar.selectbox("Choose scene", scene_options, index=0)

    with st.expander(f"Visual overview of Task {task_idx}", expanded=True):
        st.image(cached_plot(task_idx))

    _arc[task_idx].decompose()
    # Decomposition
    with st.expander(f"Decomposition of Scene {scene_idx}", expanded=True):
        left, right = st.columns(2)
        with left:
            st.image(cached_plot((task_idx, int(scene_idx), "input"), "Tree"))
        with right:
            st.image(cached_plot((task_idx, int(scene_idx), "output"), "Tree"))

    # Matching
    _arc[task_idx].match()
    with st.expander(f"Matching between the Scene's input and output", expanded=True):
        st.image(cached_plot((task_idx, int(scene_idx))))

    # Solution
    _arc[task_idx].infer()
    with st.expander(f"The Solution determined from all cases:", expanded=True):
        st.write(_arc[task_idx].solution)
