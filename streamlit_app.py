import streamlit as st
import litellm
from litellm import completion_cost
import instructor
import logging
from logging import StreamHandler, FileHandler
import os
from typing import List, Dict
from tavily import TavilyClient
from workflow_steps import WORKFLOW_STEPS, SUMMARY_BEGINNING_OF_PROMPT, SUMMARY_END_OF_PROMPT

# Set DEBUG_MODE
DEBUG_MODE = False

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

# Define required environment variables
REQUIRED_ENV = ["TAVILY_API_KEY"]

# Model selection and settings; pick sonnet or deepseek at the top
MODEL = "sonnet_vertex"
if MODEL == "sonnet_vertex":
    MODEL_NAME = "vertex_ai/claude-3-5-sonnet@20240620"
    TEMPERATURE = 0.5 #0.3-0.5 for balanced, more for creativity
    TOP_P = None #don't adjust both temp and top_p
    FREQUENCY_PENALTY = None #n/a on vertex
    PRESENCE_PENALTY = None #n/a on vertex
    REQUIRED_ENV.extend(["GOOGLE_APPLICATION_CREDENTIALS", "VERTEXAI_PROJECT", "VERTEXAI_LOCATION"])
elif MODEL == "deepseek":
    MODEL_NAME = "deepseek/deepseek-chat"
    TEMPERATURE = None
    TOP_P = None
    FREQUENCY_PENALTY = None
    PRESENCE_PENALTY = None
    REQUIRED_ENV.append("DEEPSEEK_API_KEY")
else:
    raise ValueError("Invalid MODEL_CHOICE.")

## Configure logging
# Remove any existing handlers from the root logger
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[])
logger = logging.getLogger()
# File handler
file_handler = logging.FileHandler('llm_qa.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(file_handler)
# Stream handler for console output
stream_handler = StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(stream_handler)

if DEBUG_MODE:
    os.environ['LITELLM_LOG'] = 'DEBUG'

# Set up API keys and credentials
for key in REQUIRED_ENV:
    value = os.environ.get(key)
    if value is None:
        try:
            value = st.secrets.get(key)
        except FileNotFoundError:
            st.error(f"Secret '{key}' not found. Please set it as an environment variable, in a secrets.toml file or in the Streamlit console.")
            continue
    os.environ[key] = value

instructorlitellm_client = instructor.from_litellm(litellm.completion)
try:
    tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
except KeyError:
    st.error("Error initialising Tavily client. Missing API key?")
    tavily_client = None

def prompt_model(prompt: str, max_tokens: int = 1024, role: str = "user", response_model=None, **kwargs) -> str:
    """
    Calls the LLM API with the given prompt and returns the raw response as a string.

    Args:
        prompt (str): The input prompt for the API.
        max_tokens (int, optional): The maximum number of tokens in the response. Defaults to 1024.
        role (str, optional): The role of the message sender. Defaults to "user".
        response_model (optional): The response model to use. Defaults to None.

    Returns:
        str: The raw response from the LLM API.
    """
    # Prepare parameters
    params = {
        "model": MODEL_NAME,
        "max_tokens": max_tokens,
        "messages": [{"role": role, "content": prompt}],
        "response_model": response_model,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "frequency_penalty": FREQUENCY_PENALTY,
        "presence_penalty": PRESENCE_PENALTY
    }
    params.update(kwargs)  # Add any additional kwargs

    # Log the parameters
    logging.info(f"Parameters: {params}")

    resp = instructorlitellm_client.chat.completions.create(**params)

    # Calculate and log token usage and cost
    input_tokens = resp.usage.prompt_tokens
    output_tokens = resp.usage.completion_tokens
    total_tokens = resp.usage.total_tokens
    try:
        cost = completion_cost(completion_response=resp)
        logging.info(f"Token usage - Estimated cost: ${cost:.6f}, Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
    except Exception as e:
        logging.error(f"Error calculating completion cost: {str(e)}")
        logging.info(f"Token usage - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
    
    # Log the response
    logging.info(f"Response: {resp}")

    if response_model is None:
        return resp['choices'][0]['message']['content']
    else:
        return resp.content

def run_step(step: Dict[str, str], company_url: str) -> str:
    """
    Run a single step of the workflow.

    Args:
        step (Dict[str, str]): A dictionary containing step information.
        company_url (str): The URL of the company being analyzed.

    Returns:
        str: The result of the step.
    """
    search_params = {
        "query": step["search_query"].format(company_url=company_url),
        "search_depth": "basic",
        "max_results": 5,
        "include_raw_content": True
    }
    
    if "include_domains" in step:
        include_domains = [domain.format(company_url=company_url) for domain in step["include_domains"]]
        search_params["include_domains"] = include_domains

    search_results = tavily_client.search(**search_params)
    
    # Filter out file results
    filtered_results = [result for result in search_results['results'] if not result['url'].lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.csv', '.zip','.rar'))]
    search_results['results'] = filtered_results

    # Log the search results
    logging.info(f"Search Parameters: {search_params}")
    logging.info(f"Filtered Search Results: {search_results}")
    
    prompt = f"{step['prompt_to_analyse']}\n Base this on the following search results:\n {search_results}"
    return prompt_model(prompt)

## Button to identify the model (only shown in debug mode)
if DEBUG_MODE:
    col1, col2 = st.columns(2)
    if col1.button("Test Model", use_container_width=True):
        st.session_state.model_response = prompt_model("Which model are you? Answer in format: Using model: Vendor, Model")
    col2.write(f"{st.session_state.model_response}")

# Input for company URL
st.session_state.company_url = st.text_input("Enter company URL:", value=st.session_state.company_url)

col1, col2 = st.columns(2)

col1.button("Analyze Company", on_click=analyze_company_callback, use_container_width=True)
col2.button("Summarize", on_click=summarize_callback, use_container_width=True)

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
