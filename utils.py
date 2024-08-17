import os
import logging
from typing import Dict
import litellm
from litellm import completion_cost
import instructor
from tavily import TavilyClient
from model_config import MODEL_NAME, TEMPERATURE, TOP_P, FREQUENCY_PENALTY, PRESENCE_PENALTY

# Global variables for clients
tavily_client = None
instructorlitellm_client = None

def initialize_clients():
    global tavily_client, instructorlitellm_client
    
    instructorlitellm_client = instructor.from_litellm(litellm.completion)
    try:
        tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    except KeyError:
        logging.error("Error initialising Tavily client. Missing API key?")
        tavily_client = None

def prompt_model(prompt: str, max_tokens: int = 1024, role: str = "user", response_model=None, **kwargs) -> str:
    initialize_clients()
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
    initialize_clients()
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
