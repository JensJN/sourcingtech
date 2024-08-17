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
import logging
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
if 'is_step_done' not in st.session_state:
    st.session_state.is_step_done = [False] * len(WORKFLOW_STEPS)

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


col1, _ = st.columns(2)

col1.button("Analyze Company", on_click=analyze_company_callback, use_container_width=True)

# Function to create display step functions
def create_display_step_function(step_index):
    run_every_this_step = 1.0 if st.session_state.is_step_running[step_index] else None
    @st.fragment(run_every=run_every_this_step)
    def display_step():
        # global rerun is required to reset run_every when all are done
        if st.session_state.is_step_done[step_index] and all(not st.session_state.is_step_running[i] for i in range(len(WORKFLOW_STEPS))):
            st.session_state.is_step_done[step_index] = False
            st.rerun()

        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(WORKFLOW_STEPS[step_index]["step_name"])
        with col2:
            button_text = "Run Step"
            if st.session_state.is_step_running[step_index]:
                elapsed_time = int(time.time() - st.session_state.step_start_time[step_index])
                button_text = f"Running... {elapsed_time}s"
            
            if st.button(
                button_text,
                key=f"run_step_{step_index}",
                disabled=st.session_state.is_step_running[step_index],
                use_container_width=True
            ):
                if st.session_state.company_url:
                    st.session_state.is_step_running[step_index] = True
                    st.session_state.step_start_time[step_index] = time.time()
                    
                    def work_process():
                        try:
                            result = run_step(WORKFLOW_STEPS[step_index], st.session_state.company_url)
                            st.session_state.step_results[step_index] = result
                        except Exception as e:
                            logging.error(f"Error in step {step_index}: {str(e)}")
                            st.session_state.step_results[step_index] = f"Error occurred during step {step_index}."
                        finally:
                            st.session_state.is_step_running[step_index] = False
                            st.session_state.step_start_time[step_index] = None
                            st.session_state.is_step_done[step_index] = True
                            logging.info(f"Step {step_index} work process completed")

                    thread = threading.Thread(target=work_process, daemon=True)
                    add_script_run_ctx(thread)
                    thread.start()
                    st.rerun() #required to start run_every
                else:
                    st.error("Please enter a company URL.")
        
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
        if st.button(
            button_text,
            disabled=st.session_state.is_summary_running,
            use_container_width=True
        ):
            if any(st.session_state.step_results):
                st.session_state.is_summary_running = True
                st.session_state.summary_start_time = time.time()
                
                def work_process():
                    try:
                        summary_prompt = SUMMARY_BEGINNING_OF_PROMPT + "\n\n".join(st.session_state.step_results) + SUMMARY_END_OF_PROMPT
                        result = prompt_model(summary_prompt)
                        st.session_state.final_summary = result
                    except Exception as e:
                        logging.error(f"Error in summary generation: {str(e)}")
                        st.session_state.final_summary = "Error occurred during summary generation."
                    finally:
                        st.session_state.is_summary_running = False
                        st.session_state.summary_start_time = None
                        logging.info("Summary work process completed")

                thread = threading.Thread(target=work_process, daemon=True)
                add_script_run_ctx(thread)
                thread.start()
                st.rerun() #required to start run_every
            else:
                st.error("Please analyze the company first.")
    st.text_area("", value=st.session_state.final_summary, height=200, key="final_summary")

display_summary()
