import streamlit as st
from typing import List
import threading
import time
from streamlit.runtime.scriptrunner import add_script_run_ctx
from workflow_steps import WORKFLOW_STEPS, SUMMARY_BEGINNING_OF_PROMPT, SUMMARY_END_OF_PROMPT
from env_config import setup_environment, setup_logging
from utils import prompt_model, run_step, initialize_clients

# Setup environment and logging, initialize clients
DEBUG_MODE = True # Set DEBUG_MODE = False unless debugging for dev
setup_environment()
setup_logging(debug_mode=DEBUG_MODE)
initialize_clients(mock_clients=True)

st.set_page_config(page_title="JN test - Company Analysis Workflow")
st.title("JN test - Company Analysis Workflow")

# Initialize session state
if 'company_url' not in st.session_state:
    st.session_state.company_url = ""
if 'step_results' not in st.session_state:
    st.session_state.step_results = [""] * len(WORKFLOW_STEPS)
if 'final_summary' not in st.session_state:
    st.session_state.final_summary = ""
if 'model_response' not in st.session_state:
    st.session_state.model_response = ""
if 'is_step_running' not in st.session_state:
    st.session_state.is_step_running = [False] * len(WORKFLOW_STEPS)
if 'step_start_time' not in st.session_state:
    st.session_state.step_start_time = [None] * len(WORKFLOW_STEPS)
if 'is_summary_running' not in st.session_state:
    st.session_state.is_summary_running = False
if 'summary_start_time' not in st.session_state:
    st.session_state.summary_start_time = None

## Button to identify the model (only shown in debug mode)
if DEBUG_MODE:
    col1, col2 = st.columns(2)
    if col1.button("Test Model", use_container_width=True):
        st.session_state.model_response = prompt_model("Which model are you? Answer in format: Using model: Vendor, Model")
    col2.write(f"{st.session_state.model_response}")

# Input for company URL
st.session_state.company_url = st.text_input("Enter company URL:", value=st.session_state.company_url)

def analyze_company_callback():
    if st.session_state.company_url:
        for i, step in enumerate(WORKFLOW_STEPS):
            result = run_step(step, st.session_state.company_url)
            st.session_state.step_results[i] = result
    else:
        st.error("Please enter a company URL.")

def summarize_callback():
    if any(st.session_state.step_results):
        st.session_state.is_summary_running = True
        st.session_state.summary_start_time = time.time()
        
        def work_process():
            summary_prompt = SUMMARY_BEGINNING_OF_PROMPT + "\n\n".join(st.session_state.step_results) + SUMMARY_END_OF_PROMPT
            st.session_state.final_summary = prompt_model(summary_prompt)
            st.session_state.is_summary_running = False
            st.session_state.summary_start_time = None
            st.rerun()

        thread = threading.Thread(target=work_process, daemon=True)
        add_script_run_ctx(thread)
        thread.start()
        st.rerun(scope="fragment")
    else:
        st.error("Please analyze the company first.")

def run_step_callback(step_index):
    if st.session_state.company_url:
        st.session_state.is_step_running[step_index] = True
        st.session_state.step_start_time[step_index] = time.time()
        
        def work_process():
            result = run_step(WORKFLOW_STEPS[step_index], st.session_state.company_url)
            st.session_state.step_results[step_index] = result
            st.session_state.is_step_running[step_index] = False
            st.session_state.step_start_time[step_index] = None
            st.rerun()

        thread = threading.Thread(target=work_process, daemon=True)
        add_script_run_ctx(thread)
        thread.start()
        st.rerun(scope="fragment")
    else:
        st.error("Please enter a company URL.")

col1, _ = st.columns(2)

col1.button("Analyze Company", on_click=analyze_company_callback, use_container_width=True)

# Function to create display step functions
def create_display_step_function(step_index):
    def display_step():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(WORKFLOW_STEPS[step_index]["step_name"])
        with col2:
            button_text = "Run Step"
            if st.session_state.is_step_running[step_index]:
                elapsed_time = int(time.time() - st.session_state.step_start_time[step_index])
                button_text = f"Running... {elapsed_time}s"
            st.button(
                button_text,
                key=f"run_step_{step_index}",
                on_click=run_step_callback,
                args=(step_index,),
                disabled=st.session_state.is_step_running[step_index],
                use_container_width=True
            )
        
        st.text_area("", value=st.session_state.step_results[step_index], height=150, key=f"step_{step_index}")

    return display_step

# Display step results
for i in range(len(WORKFLOW_STEPS)):
    display_step_func = create_display_step_function(i)
    # Register the function as a global
    globals()[f'display_step_{i}'] = display_step_func
    # Turn the function into a fragment with run_every set if step/thread running
    run_every_this_step = 1.0 if st.session_state.is_step_running[i] else None
    st.fragment(func=globals()[f'display_step_{i}'],run_every=run_every_this_step)
    # Call the function
    globals()[f'display_step_{i}']()

# Display final summary
@st.fragment(run_every=1.0 if st.session_state.is_summary_running else None)
def display_summary():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Final Summary")
    with col2:
        button_text = "Summarize"
        if st.session_state.is_summary_running:
            elapsed_time = int(time.time() - st.session_state.summary_start_time)
            button_text = f"Running... {elapsed_time}s"
        st.button(
            button_text,
            on_click=summarize_callback,
            disabled=st.session_state.is_summary_running,
            use_container_width=True
        )
    st.text_area("", value=st.session_state.final_summary, height=200, key="final_summary")

display_summary()
