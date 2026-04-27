import os
from dotenv import load_dotenv

# Try to load .env, if missing or incomplete, show setup UI
if not os.path.exists(".env"):
    from setup_ui import setup_api_key
    setup_api_key()

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HOTKEY = os.getenv("HOTKEY", "ctrl+alt+g")

if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_"):
    from setup_ui import setup_api_key
    setup_api_key()
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
