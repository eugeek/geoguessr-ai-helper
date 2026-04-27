import os
import sys
from pathlib import Path

if sys.platform == "win32":
    APP_DATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GeoGuessr-Helper"
else:
    APP_DATA = Path.home() / ".geoguessr-helper"

APP_DATA.mkdir(parents=True, exist_ok=True)
ENV_FILE = APP_DATA / ".env"


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


if not ENV_FILE.exists():
    from setup_ui import setup_api_key
    setup_api_key()

_load_env(ENV_FILE)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HOTKEY = os.getenv("HOTKEY", "ctrl+alt+g")
MODEL = os.getenv("MODEL", "gemini-2.5-flash-lite")

if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_"):
    from setup_ui import setup_api_key
    setup_api_key()
    _load_env(ENV_FILE)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
