import threading
import sys
from config import HOTKEY
from capture import capture_screen
from analyzer import analyze
from overlay import create_window, show_result, reset_button
import logging
import asyncio
import webview

logging.basicConfig(
    filename="geoguessr_analysis.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_processing = False


def process_screenshot() -> None:
    global _processing

    if _processing:
        return

    _processing = True

    try:
        logger.info("Screenshot capture started")
        image_bytes = capture_screen()

        logger.info("Analysis started")
        result = asyncio.run(analyze(image_bytes))

        logger.info(f"Analysis complete: {result.country} ({result.confidence}%) at {result.lat:.6f}, {result.lon:.6f}")

        show_result(result)

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        _processing = False
        reset_button()


def trigger_analyze():
    threading.Thread(target=process_screenshot, daemon=True).start()


def setup_hotkey():
    from pynput import keyboard

    parts = HOTKEY.lower().split("+")
    modifiers = set()
    key = None

    modifier_map = {
        "ctrl": keyboard.Key.ctrl,
        "alt": keyboard.Key.alt,
        "shift": keyboard.Key.shift,
        "cmd": keyboard.Key.cmd,
    }

    for part in parts:
        if part in modifier_map:
            modifiers.add(modifier_map[part])
        else:
            key = part

    pressed = set()

    def on_press(k):
        try:
            if k in modifiers:
                pressed.add(k)
            elif hasattr(k, "char") and k.char == key:
                if modifiers.issubset(pressed):
                    trigger_analyze()
        except (AttributeError, TypeError):
            pass

    def on_release(k):
        pressed.discard(k)

    keyboard.Listener(on_press=on_press, on_release=on_release).start()


def main() -> None:
    global _loop

    if sys.platform != "win32":
        print("❌ This app is Windows-only.")
        sys.exit(1)

    print(f"GeoGuessr Helper started. Hotkey: {HOTKEY}")

    try:
        setup_hotkey()
    except Exception as e:
        print(f"⚠ Hotkey setup failed: {e}")

    create_window(trigger_analyze)
    webview.start()


if __name__ == "__main__":
    main()
