import streamlit as st

from arc.app.util import cached_plot


def solver(task_idx: int):
    _arc = st.session_state.arc

    scene_options = list(range(len(_arc[task_idx].cases)))
    scene_idx = st.sidebar.selectbox("Choose scene", scene_options, index=0)

    # title = "Choose step to stop after"
    # options = ["Decomposition", "Matching"]
    # process = st.sidebar.selectbox(title, options, index=0)
    process = "Matching"
    with st.expander(f"Visual overview of Task {task_idx}", expanded=True):
        st.image(cached_plot(task_idx))

    # Decomposition
    _arc[task_idx][scene_idx].decompose()
    with st.expander(f"Decomposition of Scene {scene_idx}", expanded=True):
        left, right = st.columns(2)
        with left:
            st.image(cached_plot((task_idx, int(scene_idx), "input"), "Tree"))
        with right:
            st.image(cached_plot((task_idx, int(scene_idx), "output"), "Tree"))
    if process == "Decomposition":
        return

    # Matching
    _arc[task_idx][scene_idx].match()
    with st.expander(f"Matching between the Scene's input and output", expanded=True):
        st.image(cached_plot((task_idx, int(scene_idx)), "Match"))
    if process == "Matching":
        return
