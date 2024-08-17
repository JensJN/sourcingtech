import streamlit as st
import litellm
from litellm import completion_cost
import instructor
import logging
import os
from typing import List, Dict
from tavily import AsyncTavilyClient
from workflow_steps import WORKFLOW_STEPS, SUMMARY_BEGINNING_OF_PROMPT, SUMMARY_END_OF_PROMPT
import asyncio
import concurrent.futures
from model_config import MODEL, MODEL_NAME, TEMPERATURE, TOP_P, FREQUENCY_PENALTY, PRESENCE_PENALTY
from env_setup import setup_environment

async def main():
    # Set DEBUG_MODE
    DEBUG_MODE = True

    if DEBUG_MODE:
        os.environ['LITELLM_LOG'] = 'DEBUG'

    # Set up API keys and credentials
    setup_environment()

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

    instructorlitellm_client = instructor.from_litellm(litellm.acompletion)
    try:
        tavily_client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    except KeyError:
        st.error("Error initialising Tavily client. Missing API key?")
        tavily_client = None

    async def prompt_model(prompt: str, max_tokens: int = 1024, role: str = "user", response_model=None, **kwargs) -> str:
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

        resp = await instructorlitellm_client.chat.completions.create(**params)

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

    async def run_step(step: Dict[str, str], company_url: str) -> str:
        """
        Run a single step of the workflow.

        Args:
            step (Dict[str, str]): A dictionary containing step information.
            company_url (str): The URL of the company being analyzed.

        Returns:
            str: The result of the step.
        """
        if DEBUG_MODE: logging.info(f"Starting run_step for step: {step['step_name']}")
        search_params = {
            "query": step["search_query"].format(company_url=company_url),
            "search_depth": "basic",
            "max_results": 5,
            "include_raw_content": True
        }
    
        if "include_domains" in step:
            include_domains = [domain.format(company_url=company_url) for domain in step["include_domains"]]
            search_params["include_domains"] = include_domains
        
        if DEBUG_MODE: logging.info(f"tavily_client: running search")
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(tavily_client.search, **search_params)
                search_results = future.result()
            if DEBUG_MODE: logging.info(f"tavily_client: search completed")
        except Exception as e:
            logging.error(f"Error during Tavily search: {str(e)}")
            search_results = {"results": []}

        # Filter out file results
        filtered_results = [result for result in search_results['results'] if not result['url'].lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.csv', '.zip','.rar'))]
        search_results['results'] = filtered_results

        # Log the search results
        logging.info(f"Search Parameters: {search_params}")
        logging.info(f"Filtered Search Results: {search_results}")
    
        prompt = f"{step['prompt_to_analyse']}\n Base this on the following search results:\n {search_results}"
        return await prompt_model(prompt)

    ## Button to identify the model (only shown in debug mode)
    if DEBUG_MODE:
        col1, col2 = st.columns(2)
        if col1.button("Test Model", use_container_width=True):
            st.session_state.model_response = await prompt_model("Which model are you? Answer in format: Using model: Vendor, Model")
        if st.session_state.model_response:
            col2.write(f"{st.session_state.model_response}")

    # Input for company URL
    st.session_state.company_url = st.text_input("Enter company URL:", value=st.session_state.company_url)

    async def analyze_company_callback():
        if st.session_state.company_url:
            for i, step in enumerate(WORKFLOW_STEPS):
                result = await run_step(step, st.session_state.company_url)
                st.session_state.step_results[i] = result
        else:
            st.error("Please enter a company URL.")

    async def summarize_callback():
        if any(st.session_state.step_results):
            summary_prompt = SUMMARY_BEGINNING_OF_PROMPT + "\n\n".join(st.session_state.step_results) + SUMMARY_END_OF_PROMPT
            st.session_state.final_summary = await prompt_model(summary_prompt)
        else:
            st.error("Please analyze the company first.")

    async def run_step_callback(step_index):
        if st.session_state.company_url:
            if DEBUG_MODE: logging.info(f"run_step_callback: running await for step {step_index}")
            result = await run_step(WORKFLOW_STEPS[step_index], st.session_state.company_url)
            if DEBUG_MODE: logging.info(f"run_step_callback: Step {step_index} result: {result}")
            st.session_state.step_results[step_index] = result
        else:
            st.error("Please enter a company URL.")

    col1, col2 = st.columns(2)

    if col1.button("Analyze Company", use_container_width=True):
        asyncio.create_task(analyze_company_callback())
    if col2.button("Summarize", use_container_width=True):
        asyncio.create_task(summarize_callback())

    # Display step results
    for i, step in enumerate(WORKFLOW_STEPS):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(step["step_name"])
        with col2:
            if st.button("Run Step", key=f"run_step_{i}", use_container_width=True):
                asyncio.create_task(run_step_callback(i))
        
        st.text_area("", value=st.session_state.step_results[i], height=150, key=f"step_{i}")

    # Display final summary
    st.subheader("Final Summary")
    st.text_area("", value=st.session_state.final_summary, height=200, key="final_summary")

if __name__ == '__main__':
    asyncio.run(main())
