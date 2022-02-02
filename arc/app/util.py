import functools
import streamlit as st
import time
from io import BytesIO

from matplotlib.figure import Figure
from matplotlib import pyplot
import streamlit as st

from arc.viz import plot
from arc.arc import Index


@st.cache(allow_output_mutation=True, ttl=None)
def cached_plot(plot_idx: Index) -> BytesIO:
    _arc = st.session_state.arc
    image_buffer = BytesIO()
    fig: Figure = plot(_arc[plot_idx], show_axis=False)
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


# def logger() -> None:
#     msg = st.session_state.logs
#     with logger.container():
#         st.markdown(
#             f'<p style="background-color:#bbbbbb;font-size:16px;">{msg}</p>',
#             unsafe_allow_html=True,
#         )
