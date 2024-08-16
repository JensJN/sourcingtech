import streamlit as st
import litellm
import instructor

## DEBUG only
#litellm.set_verbose=True

## Requires env vars to be set for API keys in: 
# DEEPSEEK_API_KEY or ANTHROPIC_API_KEY
# or GOOGLE_APPLICATION_CREDENTIALS, VERTEXAI_PROJECT, VERTEXAI_LOCATION

## Model name and settings
#MODEL_NAME = "deepseek/deepseek-chat"
MODEL_NAME="vertex_ai/claude-3-5-sonnet@20240620"

# Default parameters for model behavior
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 1.0
DEFAULT_FREQUENCY_PENALTY = 0.0
DEFAULT_PRESENCE_PENALTY = 0.0

client = instructor.from_litellm(litellm.completion)
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
        "temperature": DEFAULT_TEMPERATURE,
        "top_p": DEFAULT_TOP_P,
        "frequency_penalty": DEFAULT_FREQUENCY_PENALTY,
        "presence_penalty": DEFAULT_PRESENCE_PENALTY,
    }
    params.update(kwargs)  # Add any additional kwargs

    resp = client.chat.completions.create(**params)
    if response_model is None:
        return resp['choices'][0]['message']['content']
    else:
        return resp.content

st.write('Sourcing tech test JN')

## Print which model we're using
model_response = prompt_model("which model provider and version are you? one-line answer max.")
st.write(f"Using model: {model_response}")

