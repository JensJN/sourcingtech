import os
import streamlit as st
from model_config import REQUIRED_ENV

def setup_environment():
    """Set up API keys and credentials from environment variables or Streamlit secrets."""
    for key in REQUIRED_ENV:
        value = os.environ.get(key)
        if value is None:
            try:
                value = st.secrets.get(key)
            except FileNotFoundError:
                st.error(f"Secret '{key}' not found. Please set it as an environment variable, in a secrets.toml file or in the Streamlit console.")
                continue
        os.environ[key] = value
