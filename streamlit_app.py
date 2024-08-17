import streamlit as st
import logging
from typing import List
from workflow_steps import WORKFLOW_STEPS, SUMMARY_BEGINNING_OF_PROMPT, SUMMARY_END_OF_PROMPT
from env_config import setup_environment, setup_logging
from utils import prompt_model, run_step

# Setup environment and logging
DEBUG_MODE = True # Set DEBUG_MODE = False unless debugging for dev
setup_environment()
setup_logging()

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
        result = run_step(WORKFLOW_STEPS[step_index], st.session_state.company_url)
        st.session_state.step_results[step_index] = result
    else:
        st.error("Please enter a company URL.")

col1, col2 = st.columns(2)

col1.button("Analyze Company", on_click=analyze_company_callback, use_container_width=True)
col2.button("Summarize", on_click=summarize_callback, use_container_width=True)

# Display step results
for i, step in enumerate(WORKFLOW_STEPS):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(step["step_name"])
    with col2:
        st.button("Run Step", key=f"run_step_{i}", on_click=run_step_callback, args=(i,), use_container_width=True)
    
    st.text_area("", value=st.session_state.step_results[i], height=150, key=f"step_{i}")

# Display final summary
st.subheader("Final Summary")
st.text_area("", value=st.session_state.final_summary, height=200, key="final_summary")
