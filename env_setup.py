import os
import streamlit as st
import logging
from logging import StreamHandler, FileHandler
from model_config import REQUIRED_ENV

def setup_environment():
    # Configure logging
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[])
    logger = logging.getLogger()
    # File handler
    file_handler = FileHandler('llm_qa.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(file_handler)
    # Stream handler for console output
    stream_handler = StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(stream_handler)
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
