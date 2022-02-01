import functools
import streamlit as st
import time
from io import BytesIO

from matplotlib.figure import Figure
from matplotlib import pyplot
import streamlit as st

from arc.viz import plot_grid, plot_layout
from arc.layouts import match_layout, tree_layout, task_layout
from arc.arc import Index


@st.cache(allow_output_mutation=True, ttl=None)
def cached_plot(plot_idx: Index, plot_type: str = None) -> BytesIO:
    _arc = st.session_state.arc
    image_buffer = BytesIO()
    if plot_type == "Tree":
        fig: Figure = plot_layout(tree_layout(_arc[plot_idx]), show_axis=False)
    elif plot_type == "Match":
        fig: Figure = plot_layout(match_layout(_arc[plot_idx]), show_axis=False)
    else:
        match plot_idx:
            case int(task_idx):
                fig: Figure = plot_layout(task_layout(_arc[task_idx]))
            case (task_idx, scene_idx):
                fig: Figure = plot_grid(_arc[(task_idx, scene_idx)].input.rep.grid)
            case _:
                return image_buffer

    fig.savefig(image_buffer, format="png")
    pyplot.close(fig)
    return image_buffer


def timed(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        dt = time.time() - t1
        st.write(f"...finished in {dt:.3f}s")
        return result

    return wrapped
