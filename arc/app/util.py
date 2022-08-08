from io import BytesIO

import streamlit as st
from arc.arc import Index
from arc.viz import plot
from matplotlib import pyplot
from matplotlib.figure import Figure


def cached_plot(
    plot_idx: Index, attribute: str | None = None, cache: bool = True
) -> BytesIO:
    full_idx = (plot_idx, attribute)
    _arc = st.session_state.arc
    plot_cache = st.session_state.plot_cache
    if full_idx in plot_cache:
        return plot_cache[full_idx]

    image_buffer = BytesIO()
    if attribute is not None:
        fig: Figure = plot(getattr(_arc[plot_idx], attribute))
    else:
        fig: Figure = plot(_arc[plot_idx])
    fig.savefig(image_buffer, format="png")
    pyplot.close(fig)
    if cache:
        plot_cache[full_idx] = image_buffer
    return image_buffer
