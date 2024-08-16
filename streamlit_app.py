import streamlit as st
import litellm
from litellm import completion_cost
import instructor
import logging
from logging import StreamHandler, FileHandler
import os
from typing import List, Dict
from tavily import TavilyClient
from workflow_steps import WORKFLOW_STEPS

st.set_page_config(page_title="JN test - Company Analysis Workflow")
st.title("JN test - Company Analysis Workflow")

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
#os.environ['LITELLM_LOG'] = 'DEBUG' ## for DEBUG only, otherwise keep commented out

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
        "include_raw_content": True,
        "exclude_domains": [".pdf", ".doc", ".docx", ".txt"]
    }
    
    if "include_domains" in step:
        include_domains = [domain.format(company_url=company_url) for domain in step["include_domains"]]
        search_params["include_domains"] = include_domains

    search_results = tavily_client.search(**search_params)
    
    # Log the search results
    logging.info(f"Search Parameters: {search_params}")
    logging.info(f"Search Results: {search_results}")
    
    prompt = f"{step['prompt_to_analyse']}\n Base this on the following search results:\n {search_results}"
    return prompt_model(prompt)

## Button to identify the model
col1, col2 = st.columns([1, 3])
if col1.button("Test Model"):
    model_response = prompt_model("Which model are you? Answer in format: Vendor; Model")
    col2.write(f"Using model: {model_response}")

# Input for company URL
company_url = st.text_input("Enter company URL:")

if st.button("Analyze Company"):
    if company_url:
        # Run each step of the workflow
        step_results = []
        for step in WORKFLOW_STEPS:
            st.subheader(step["step_name"])
            result = run_step(step, company_url)
            st.write(result)
            step_results.append(result)

        # Final summary step
        st.subheader("Final Summary")
        summary_prompt = f"""I'm a VC. I want to draft an email to an entrepreneur that conveys that I'm knowledgeable about:
        - his business
        - the market and industry context his business operates in
        - how his business differentiates vs. its competitors
        - what customers are saying about his business
        - any recent news or key developments around his business I might congratulate him on
        Be concise and base this on the following information:
        """ + "\n\n".join(step_results)
        final_summary = prompt_model(summary_prompt)
        st.write(final_summary)
    else:
        st.error("Please enter a company URL.")
