import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HOTKEY = os.getenv("HOTKEY", "ctrl+alt+g")

if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY not found in .env file. "
        "Please set it: echo 'GEMINI_API_KEY=your_key' > .env"
    )
