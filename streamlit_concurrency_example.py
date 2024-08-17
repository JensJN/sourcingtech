import streamlit as st
from streamlit import session_state as ss
import numpy as np
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx
import time


if 'is_btn_disabled' not in ss:
    ss.is_btn_disabled = False


def simple_chart():
    color_dict = {
        'midnightblue': 'rgb(25, 25, 112)',
        'indigo': 'rgb(75, 0, 130)',
        'red': 'rgb(255, 0, 0)',
        'slategray': 'rgb(112, 128, 144)'
    }
    with st.container(border=True):
        st.markdown('This will be run from the main thread.')
        selected_color = st.selectbox('Bar Color', options=list(color_dict.keys()))
        val = st.slider("Number of bars", 1, 20, 4)
        st.bar_chart(np.random.default_rng().random(val), height=200, color=color_dict[selected_color])


def process_cb():
    ss.is_btn_disabled = True  # disable button


def work_process(njobs):
    done = 0

    while done < njobs:
        time.sleep(2)
        done += 1

    ss.is_btn_disabled = False  # enable button


@st.experimental_fragment
def analysis():
    with st.container(border=True):
        st.markdown('The process will be run from a different thread and reruns will be executed within the function only.')

        num_jobs = st.number_input('Number of jobs', value=8, min_value=5, max_value=100, step=1)

        st.button('start process', on_click=process_cb, disabled=ss.is_btn_disabled, type='primary')

        if ss.is_btn_disabled:
            wt = threading.Thread(target=work_process, args=(num_jobs,), daemon=True)
            add_script_run_ctx(wt)
            wt.start()
            wt.join()

            # Rerun to redraw the button as enabled.
            st.rerun()


def main():
    # Run in main thread.
    simple_chart()

    # Run in a separate thread.
    analysis()


if __name__ == '__main__':
    main()