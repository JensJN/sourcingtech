# Initialize REQUIRED_ENV
REQUIRED_ENV = ["TAVILY_API_KEY"]

# Model selection and settings
MODEL = "sonnet_vertex"

if MODEL == "sonnet_vertex":
    MODEL_NAME = "vertex_ai/claude-3-5-sonnet@20240620"
    TEMPERATURE = 0.5  # 0.3-0.5 for balanced, more for creativity
    TOP_P = None  # don't adjust both temp and top_p
    FREQUENCY_PENALTY = None  # n/a on vertex
    PRESENCE_PENALTY = None  # n/a on vertex
    REQUIRED_ENV.extend(["GOOGLE_APPLICATION_CREDENTIALS", "VERTEXAI_PROJECT", "VERTEXAI_LOCATION"])
elif MODEL == "gpt4o_openai":
    MODEL_NAME = "gpt-4o"
    TEMPERATURE = 0.4  # 0.3-0.5 for balanced, more for creativity
    REQUIRED_ENV.append("OPENAI_API_KEY")
elif MODEL == "deepseek":
    MODEL_NAME = "deepseek/deepseek-chat"
    TEMPERATURE = None
    TOP_P = None
    FREQUENCY_PENALTY = None
    PRESENCE_PENALTY = None
    REQUIRED_ENV.append("DEEPSEEK_API_KEY")
else:
    raise ValueError("Invalid MODEL_CHOICE.")
