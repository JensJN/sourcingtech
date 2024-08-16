import streamlit as st
import litellm
import instructor

## DEBUG only
#litellm.set_verbose=True

## Requires env vars to be set for API keys in: 
# DEEPSEEK_API_KEY or ANTHROPIC_API_KEY
# or GOOGLE_APPLICATION_CREDENTIALS, VERTEXAI_PROJECT, VERTEXAI_LOCATION

## Model selection and settings; pick sonnet or deepseek at the top
MODEL = "sonnet"
if MODEL == "sonnet":
    MODEL_NAME = "vertex_ai/claude-3-5-sonnet@20240620"
    TEMPERATURE = 0.5 #0.3-0.5 for balanced, more for creativity
    TOP_P = None #don't adjust both temp and top_p
    FREQUENCY_PENALTY = None #n/a on vertex
    PRESENCE_PENALTY = None #n/a on vertex
elif MODEL == "deepseek":
    MODEL_NAME = "deepseek/deepseek-chat"
    TEMPERATURE = None
    TOP_P = None
    FREQUENCY_PENALTY = None
    PRESENCE_PENALTY = None
else:
    raise ValueError("Invalid MODEL_CHOICE.")

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
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "frequency_penalty": FREQUENCY_PENALTY,
        "presence_penalty": PRESENCE_PENALTY
    }
    params.update(kwargs)  # Add any additional kwargs

    resp = client.chat.completions.create(**params)
    if response_model is None:
        return resp['choices'][0]['message']['content']
    else:
        return resp.content

st.write('Sourcing tech test JN')

## Button to identify the model
if st.button("Identify Model"):
    model_response = prompt_model("What model are you? Answer in format: Vendor; Model")
    st.write(f"Using model: {model_response}")

