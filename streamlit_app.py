import streamlit as st
import litellm
import instructor

## DEBUG only
#litellm.set_verbose=True

## Requires env vars to be set for API keys in: 
# DEEPSEEK_API_KEY or ANTHROPIC_API_KEY
# or GOOGLE_APPLICATION_CREDENTIALS, VERTEXAI_PROJECT, VERTEXAI_LOCATION

## Model name and settings
MODEL_NAME = "deepseek/deepseek-chat"
client = instructor.from_litellm(litellm.completion)
def prompt_model(prompt: str, max_tokens: int = 1024, role: str = "user", **kwargs) -> str:
    """
    Calls the LLM API with the given prompt and returns the raw response as a string.

    Args:
        prompt (str): The input prompt for the API.
        max_tokens (int, optional): The maximum number of tokens in the response. Defaults to 1024.
        role (str, optional): The role of the message sender. Defaults to "user".

    Returns:
        str: The raw response from the LLM API.
    """
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=max_tokens,
        messages=[
            {
                "role": role,
                "content": prompt,
            }
        ],
        **kwargs
    )
    return resp['choices'][0]['message']['content']

st.write('Sourcing tech test JN')
