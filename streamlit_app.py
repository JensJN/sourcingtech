import streamlit as st
st.set_page_config(page_title="Company Research Workflow") # needs to stay here to avoid issues

from typing import List, Callable
import threading
import time
from streamlit.runtime.scriptrunner import add_script_run_ctx
from workflow_steps import WORKFLOW_STEPS, SUMMARY_BEGINNING_OF_PROMPT, SUMMARY_END_OF_PROMPT, DRAFT_EMAIL_PROMPT
from env_config import setup_environment, setup_logging
from utils import prompt_model, run_step, initialize_clients
import base64
from weasyprint import HTML
from io import BytesIO

# Setup environment and logging, initialize clients, setup cache for slow/expensive functions
DEBUG_MODE = False # remember to set DEBUG_MODE = False before deploying
setup_environment()
setup_logging(debug_mode=DEBUG_MODE)
import logging
initialize_clients(mock_clients=False) # DEBUG; remember to disable before deploying

from diskcache import Cache
cache = Cache('/tmp/mycache')

st.title("Company Research Workflow")
st.header("JN test")
st.write("")

# Initialize session state
if 'company_url' not in st.session_state:
    st.session_state.company_url = ""
if 'step_results' not in st.session_state:
    st.session_state.step_results = [""] * len(WORKFLOW_STEPS)
if 'summary_result' not in st.session_state:
    st.session_state.summary_result = ""
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
if 'is_summary_done' not in st.session_state:
    st.session_state.is_summary_done = False
if 'summary_queued' not in st.session_state:
    st.session_state.summary_queued = False
if 'is_draft_email_running' not in st.session_state:
    st.session_state.is_draft_email_running = False
if 'draft_email_start_time' not in st.session_state:
    st.session_state.draft_email_start_time = None
if 'is_draft_email_done' not in st.session_state:
    st.session_state.is_draft_email_done = False
if 'draft_email_queued' not in st.session_state:
    st.session_state.draft_email_queued = False
if 'draft_email_result' not in st.session_state:
    st.session_state.draft_email_result = ""

def get_is_any_process_running():
    return any(st.session_state.is_step_running) or st.session_state.is_summary_running or st.session_state.is_draft_email_running

def get_is_analysis_running():
    return get_is_any_process_running() or st.session_state.summary_queued or st.session_state.draft_email_queued

def get_is_anything_marked_done():
    return st.session_state.is_summary_done or st.session_state.is_draft_email_done or any(st.session_state.is_step_done)

def set_everthing_not_done():
    st.session_state.is_summary_done = False
    st.session_state.is_draft_email_done = False
    st.session_state.is_step_done = [False] * len(WORKFLOW_STEPS)

#@st.cache_data # bug in streamlit 1.37 causes cached functions to not be thread safe (https://github.com/streamlit/streamlit/issues/9260)
@cache.memoize()
def cached_prompt_model(prompt: str, max_tokens: int = 1024, role: str = "user", response_model=None, **kwargs):
    returnval = prompt_model(prompt, max_tokens, role, response_model, **kwargs)
    return returnval

#@st.cache_data# bug in streamlit 1.37 causes cached functions to not be thread safe (https://github.com/streamlit/streamlit/issues/9260)
@cache.memoize()
def cached_run_step(step: dict, company_url: str):
    returnval = run_step(step, company_url)
    return returnval

def run_step_helper(step_index: int):
    if st.session_state.company_url:
        st.session_state.is_step_running[step_index] = True
        st.session_state.step_start_time[step_index] = time.time()
        
        def work_process():
            try:
                company_url = st.session_state.company_url
                result = cached_run_step(WORKFLOW_STEPS[step_index], company_url)
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
    else:
        st.error("Please enter a company URL.")

def run_summary_helper():
    if any(st.session_state.step_results):
        st.session_state.is_summary_running = True
        st.session_state.summary_start_time = time.time()
        summary_prompt = SUMMARY_BEGINNING_OF_PROMPT + "\n ***** \n" + "\n\n".join(st.session_state.step_results) + "\n ***** \n" + SUMMARY_END_OF_PROMPT
        def work_process():
            try:
                result = cached_prompt_model(summary_prompt)
                st.session_state.summary_result = result
            except Exception as e:
                logging.error(f"Error in summary generation: {str(e)}")
                st.session_state.summary_result = "Error occurred during summary generation."
            finally:
                st.session_state.is_summary_running = False
                st.session_state.summary_start_time = None
                st.session_state.is_summary_done = True
                logging.info("Summary work process completed")

        thread = threading.Thread(target=work_process, daemon=True)
        add_script_run_ctx(thread)
        thread.start()
    else:
        st.error("No results to analyze.")

def run_draft_email_helper():
    if st.session_state.summary_result:
        st.session_state.is_draft_email_running = True
        st.session_state.draft_email_start_time = time.time()
        draft_email_prompt = DRAFT_EMAIL_PROMPT + "\n ***** \n" + st.session_state.summary_result
        def work_process():
            try:
                result = cached_prompt_model(draft_email_prompt)
                st.session_state.draft_email_result = result
            except Exception as e:
                logging.error(f"Error in draft email step: {str(e)}")
                st.session_state.draft_email_result = "Error occurred during draft email step."
            finally:
                st.session_state.is_draft_email_running = False
                st.session_state.draft_email_start_time = None
                st.session_state.is_draft_email_done = True
                logging.info("Draft email work process completed")

        thread = threading.Thread(target=work_process, daemon=True)
        add_script_run_ctx(thread)
        thread.start()
    else:
        st.error("No summary to draft email from.")

## Button to identify the model (only shown in debug mode)
if DEBUG_MODE:
    col1, col2 = st.columns(2)
    if col1.button("Test Model", use_container_width=True):
        result = cached_prompt_model("Which model are you? Answer in format: Using model: Vendor, Model")
        st.session_state.model_response = result
    col2.write(f"{st.session_state.model_response}")

@st.fragment(run_every=1.0 if get_is_analysis_running() else None)
def display_analyze_company():
    # Check if summary is queued and no process is running
    if not get_is_any_process_running() and st.session_state.summary_queued:
        run_summary_helper()
        st.session_state.draft_email_queued = True  # Queue draft email step after summary is completed 
        st.session_state.summary_queued = False # Do after queuing in case of rerun race gone wrong
    # Check if draft email is queued and no process is running
    elif not get_is_any_process_running() and st.session_state.draft_email_queued:
        run_draft_email_helper()
        st.session_state.draft_email_queued = False
    # Input for company URL
    st.session_state.company_url = st.text_input("Enter company URL:", 
                                                 value=st.session_state.company_url, 
                                                 disabled=get_is_any_process_running())

    button_text = "Analyze Company"
    if get_is_any_process_running():
        running_steps = [i for i, running in enumerate(st.session_state.is_step_running) if running]
        if running_steps:
            step_index = running_steps[0]
            elapsed_time = int(time.time() - st.session_state.step_start_time[step_index])
            button_text = f"Running Step {step_index + 1}... {elapsed_time}s"
        elif st.session_state.is_summary_running:
            elapsed_time = int(time.time() - st.session_state.summary_start_time)
            button_text = f"Running Summary... {elapsed_time}s"
        elif st.session_state.is_draft_email_running:
            elapsed_time = int(time.time() - st.session_state.draft_email_start_time)
            button_text = f"Drafting Email... {elapsed_time}s"

    if st.button(button_text, use_container_width=True, disabled=get_is_any_process_running()):
        if st.session_state.company_url: # keep this check even if redundant to avoid re-run
            for i in range(len(WORKFLOW_STEPS)):
                run_step_helper(i)
            st.session_state.summary_queued = True
            st.rerun() #required to start run_every for fragments
        else:
            st.error("Please enter a company URL.")

display_analyze_company()

# Function to create display step functions
def create_display_step_function(step_index):
    @st.fragment(run_every=1.0 if (st.session_state.is_step_running[step_index] or get_is_analysis_running()) else None)
    def display_step():
        error_message = None

        st.write("") #create space
        st.write("") #create space
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
                if st.session_state.company_url: # keep this check even if redundant to avoid re-run
                    run_step_helper(step_index)
                    st.rerun() #required to start run_every for fragment
                else:
                    error_message = "Please enter a company URL."
        
        if error_message: st.error(error_message) # used to print below column, not in column
        st.text_area("Output:", value=st.session_state.step_results[step_index], height=150, key=f"step_{step_index}")

    return display_step

# Display step results; this two-step process is required to make @st.fragment or other decoration work
for i in range(len(WORKFLOW_STEPS)):
    display_step_func = create_display_step_function(i)
    # Register the function as a global
    globals()[f'display_step_{i}'] = display_step_func 
    # Call the function
    globals()[f'display_step_{i}']()

# Display final summary
@st.fragment(run_every=1.0 if (st.session_state.is_summary_running or get_is_analysis_running()) else None)
def display_summary():
    error_message = None

    st.write("") #create space
    st.write("") #create space
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
            if any(st.session_state.step_results): # keep this check even if redundant to avoid re-run
                run_summary_helper()
                st.rerun() #required to start run_every for fragment
            else:
                error_message = "No results to analyze."
    
    if error_message: st.error(error_message) # used to print below column, not in column
    st.text_area("Output:", value=st.session_state.summary_result, height=400, key="final_summary")

display_summary()

# Display draft email
@st.fragment(run_every=1.0 if (st.session_state.is_draft_email_running or get_is_analysis_running()) else None)
def display_draft_email():
    error_message = None

    st.write("") #create space
    st.write("") #create space
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Draft Email")
    with col2:
        button_text = "Draft Email"
        if st.session_state.is_draft_email_running:
            elapsed_time = int(time.time() - st.session_state.draft_email_start_time)
            button_text = f"Drafting... {elapsed_time}s"
        if st.button(
            button_text,
            disabled=st.session_state.is_draft_email_running,
            use_container_width=True
        ):
            if st.session_state.summary_result: # keep this check even if redundant to avoid re-run
                run_draft_email_helper()
                st.rerun() #required to start run_every for fragment
            else:
                error_message = "No summary to draft email from."
    
    if error_message: st.error(error_message) # used to print below column, not in column
    st.text_area("Output:", value=st.session_state.draft_email_result, height=400, key="draft_email")

display_draft_email()

def generate_pdf():
    html_template = """
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                color: black;
                font-size: 12px;
            }}
            h1, h2 {{
                color: #00008B;  /* Dark Blue */
            }}
            h1 {{
                font-size: 18px;
                margin-bottom: 10px;
            }}
            h2 {{
                font-size: 16px;
                margin-bottom: 5px;
            }}
            .section {{
                margin-bottom: 15px;
            }}
        </style>
    </head>
    <body>
        <h1>Company Analysis Report</h1>
        
        <div class="section">
            <h2>Draft Email</h2>
            <p>{draft_email}</p>
        </div>
        
        <div class="section">
            <h2>Final Summary</h2>
            <p>{summary}</p>
        </div>
        
        {steps}
    </body>
    </html>
    """
    
    steps_html = []
    for i in range(len(WORKFLOW_STEPS)):
        step_html = """
        <div class="section">
            <h2>Step {step_number}: {step_name}</h2>
            <p>{step_result}</p>
        </div>
        """.format(
            step_number=i+1,
            step_name=WORKFLOW_STEPS[i]['step_name'],
            step_result=st.session_state.step_results[i].replace('\n', '<br>')
        )
        steps_html.append(step_html)
    
    html_content = html_template.format(
        draft_email=st.session_state.draft_email_result.replace('\n', '<br>'),
        summary=st.session_state.summary_result.replace('\n', '<br>'),
        steps=''.join(steps_html)
    )
    
    pdf_file = BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file

# Download PDF button
st.write("")
if st.download_button(
    label="Download as PDF",
    data=generate_pdf(),
    file_name="company_analysis.pdf",
    mime="application/pdf",
    use_container_width=True
):
    st.success("PDF generated successfully!")

# invisible fragment to trigger global rerun to reset all fragments' run_every once nothing is running anymore; should always stay at end of file
@st.fragment(run_every=1.0 if (get_is_any_process_running() or get_is_analysis_running()) else None)
def invisible_fragment_to_rerun_when_all_done():
    #trigger rerun if any steps are marked done and nothing is running anymore
    if get_is_anything_marked_done() and not (get_is_any_process_running() or get_is_analysis_running()):
        set_everthing_not_done()
        st.rerun()
invisible_fragment_to_rerun_when_all_done()
