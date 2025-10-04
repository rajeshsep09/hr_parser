import os
from dotenv import load_dotenv

# Load environment variables from env.sample file (if it exists and is readable)
try:
    load_dotenv("env.sample")
except Exception:
    # If env.sample file has issues, continue with environment variables
    pass

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hyperrecruit")

MAX_INPUT_CHARS = int(os.getenv("HRP_MAX_INPUT_CHARS", "180000"))
MAX_OUTPUT_TOKENS = int(os.getenv("HRP_MAX_OUTPUT_TOKENS", "3000"))
USE_MOCK = os.getenv("HRP_USE_MOCK", "false").lower() == "true"
