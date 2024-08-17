import streamlit as st
from typing import List
import threading
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
        summary_prompt = SUMMARY_BEGINNING_OF_PROMPT + "\n\n".join(st.session_state.step_results) + SUMMARY_END_OF_PROMPT
        st.session_state.final_summary = prompt_model(summary_prompt)
    else:
        st.error("Please analyze the company first.")

def run_step_callback(step_index):
    if st.session_state.company_url:
        st.session_state.is_step_running[step_index] = True
        
        def work_process():
            result = run_step(WORKFLOW_STEPS[step_index], st.session_state.company_url)
            st.session_state.step_results[step_index] = result
            st.session_state.is_step_running[step_index] = False
            st.rerun()

        thread = threading.Thread(target=work_process, daemon=True)
        add_script_run_ctx(thread)
        thread.start()
    else:
        st.error("Please enter a company URL.")

col1, col2 = st.columns(2)

col1.button("Analyze Company", on_click=analyze_company_callback, use_container_width=True)
col2.button("Summarize", on_click=summarize_callback, use_container_width=True)

# Function to create display step functions
def create_display_step_function(step_index):
    run_every_this_step = 1 if st.session_state.is_step_running[step_index] else None
    @st.fragment(run_every=run_every_this_step)
    def display_step():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(WORKFLOW_STEPS[step_index]["step_name"])
        with col2:
            st.button(
                "Run Step" if not st.session_state.is_step_running[step_index] else "Running...",
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
    # Call the function
    globals()[f'display_step_{i}']()

# Display final summary
@st.fragment()
def display_summary():
    st.subheader("Final Summary")
    st.text_area("", value=st.session_state.final_summary, height=200, key="final_summary")

display_summary()
