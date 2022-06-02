import streamlit as st

from arc.arc import ARC
from arc.app.explorer import explorer
from arc.app.solver import solver
from arc.app.settings import Settings


def run_ui(start_mode: str = "Dev", n: int = Settings.N) -> None:
    """Central UI logic governing components to display."""
    init_session()
    mode_selector(start_mode, n)
    task_filter()
    task_selector()

    if st.session_state.task_idx > 0:
        solver(task_idx=st.session_state.task_idx)
    else:
        explorer()


def init_session() -> None:
    if "arc" not in st.session_state:
        st.session_state.arc = None


def mode_selector(start_mode: str, n: int) -> None:
    options = ["Demo", "Stats", "Dev"]
    st.sidebar.selectbox(
        "Select a mode", options, key="mode", index=options.index(start_mode)
    )

    # Demo mode has all solutions precalculated, can be used for filtering
    if st.session_state.mode == "Demo":
        _arc = ARC(N=n, folder=Settings.folder)
        _arc.solve_tasks()
    # Stats mode decomposes all boards for filtering (WIP)
    elif st.session_state.mode == "Stats":
        _arc = ARC(N=n, folder=Settings.folder)
    # Dev mode is the default
    else:
        _arc = ARC(N=n, folder=Settings.folder)

    st.session_state.arc = _arc


def task_filter() -> None:
    if st.session_state.arc is None:
        st.write("No ARC dataset loaded")
        return
    _arc = st.session_state.arc
    _arc.scan()
    title = "Filter tasks"
    options = sorted(_arc.stats.keys())

    def labeler(option: int) -> str:
        return f"{option} ({_arc.stats[option]})"

    st.sidebar.multiselect(title, options, format_func=labeler, key="filters")  # type: ignore


def task_selector() -> None:
    if st.session_state.arc is None:
        st.write("No ARC dataset loaded")
        return
    title = "Choose a task"
    _arc = st.session_state.arc
    _arc.select(set(st.session_state.filters))
    options = [0] + list(sorted(_arc.selection))

    def labeler(option: int) -> str:
        if option == 0:
            return "Explore"
        return str(option)

    st.sidebar.selectbox(title, options, index=0, format_func=labeler, key="task_idx")  # type: ignore
