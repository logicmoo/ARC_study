import streamlit as st
from arc.app.explorer import explorer
from arc.app.settings import Settings
from arc.app.solver import solution
from arc.arc import ARC


def run_ui(start_mode: str = "Dev", n: int = Settings.N) -> None:
    """Central UI logic governing components to display."""
    init_session()
    # mode_selector(start_mode, n)
    task_filter()
    task_selector()

    if st.session_state.task_idx > 0:
        solution(task_idx=st.session_state.task_idx)
    else:
        explorer()


def init_session() -> None:
    if "arc" not in st.session_state:
        _arc = ARC.load("demo_run")
        st.session_state.arc = _arc
        st.session_state.plot_cache = {}


def mode_selector(start_mode: str, n: int) -> None:
    options = ["Demo", "Stats", "Dev"]
    st.sidebar.selectbox(  # type: ignore
        "Select a mode", options, key="mode", index=options.index(start_mode)
    )

    # Demo mode has all solutions precalculated, can be used for filtering
    if st.session_state.mode == "Demo":
        _arc = ARC.load("demo_run")
    # Stats mode decomposes all boards for filtering (WIP)
    elif st.session_state.mode == "Stats":
        _arc = ARC(N=n, folder=Settings.folder)
    # Dev mode is the default
    else:
        _arc = ARC(N=n, folder=Settings.folder)

    st.session_state.arc = _arc


def task_filter() -> None:
    if st.session_state.arc is None:
        st.write("No ARC dataset loaded")  # type: ignore

        return
    _arc = st.session_state.arc
    _arc.scan()
    title = "Filter tasks"
    options = sorted(_arc.stats.keys())

    def labeler(option: int) -> str:
        return f"{option} ({_arc.stats[option]})"

    default: list[str] = []
    if "Solved" in options:
        default = ["Solved"]

    st.sidebar.multiselect(title, options, default=default, format_func=labeler, key="filters")  # type: ignore


def task_selector() -> None:
    if st.session_state.arc is None:
        st.write("No ARC dataset loaded")  # type: ignore

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
