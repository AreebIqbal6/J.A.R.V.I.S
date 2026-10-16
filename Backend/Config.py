import os
from dotenv import dotenv_values
from groq import Groq

# Load environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
env_vars = dotenv_values(ENV_PATH)
GROQ_API_KEY = env_vars.get("GroqAPIKey") or os.environ.get("GroqAPIKey")

# Canonical verified active models on user's Groq account
PRIMARY_MODEL = "qwen/qwen3.8-27b"
FAST_MODEL = "openai/gpt-oss-20b"
LARGE_MODEL = "openai/gpt-oss-120b"
DEFAULT_MAX_TOKENS = 400

_cached_groq_client = None

def get_groq_client() -> Groq:
    global _cached_groq_client
    if _cached_groq_client is None:
        _cached_groq_client = Groq(api_key=GROQ_API_KEY)
    return _cached_groq_client
