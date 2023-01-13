import streamlit as st
from arc.app.explorer import explorer
from arc.app.settings import Settings
from arc.app.task_display import task_display
from arc.arc import ARC


def run_ui(pickle_id: str = Settings.default_pickle_id) -> None:
    """Central UI logic governing components to display."""

    init_session(pickle_id)
    sidebar()

    if st.session_state.task_idx > 0:
        task_display(task_idx=st.session_state.task_idx)
    else:
        explorer()


def init_session(pickle_id: str = "") -> None:
    if "arc" not in st.session_state:
        container = st.empty()  # type: ignore
        container.markdown("_Loading ARC Dataset..._")  # type: ignore
        if pickle_id:
            _arc = ARC.load(pickle_id)
        else:
            _arc = ARC(N=Settings.N)
            _arc.set_log(40)
        st.session_state.arc = ARC()
        st.session_state.plot_cache = {}
        container.empty()  # type: ignore


def sidebar() -> None:
    """Everything displayed on the sidebar."""
    task_filter()
    task_selector()
    annotations()


def annotations() -> None:
    """Tickbox to hide the annotations around the app."""
    st.sidebar.checkbox("Hide annotations", key="hide_annotations")


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
    if "solved" in options:
        default = ["solved"]

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
