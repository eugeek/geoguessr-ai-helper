import asyncio
import threading
import sys
from config import HOTKEY
from capture import capture_screen
from analyzer import analyze
from overlay import show_result, set_last_screenshot
from button import FloatingButton
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename="geoguessr_analysis.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_loop = None
_loop_thread = None
_processing = False
_floating_button = None


async def process_screenshot() -> None:
    """Capture, analyze, and display result."""
    global _processing

    if _processing:
        return

    _processing = True

    try:
        print("[►] Capturing full screen...")
        logger.info("Screenshot capture started")
        image_bytes = capture_screen()
        set_last_screenshot(image_bytes)

        print("[◌] Analyzing with Gemini...")
        logger.info("Analysis started")
        result = await analyze(image_bytes)

        print(f"[✓] {result.country} (confidence: {result.confidence}%)")
        print(f"    Location: {result.lat:.6f}, {result.lon:.6f}")
        print(f"    {result.explanation}\n")

        logger.info(
            f"Analysis complete: {result.country} "
            f"({result.confidence}%) at {result.lat:.6f}, {result.lon:.6f}"
        )

        show_result(result)

    except Exception as e:
        print(f"[✗] Error: {e}")
        logger.error(f"Error during analysis: {str(e)}")
    finally:
        _processing = False


def run_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Run asyncio event loop in background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def setup_hotkey_listener_windows() -> None:
    """Windows: Setup global hotkey using pynput."""
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

    pressed_keys = set()

    def on_press(kb_key):
        try:
            if kb_key in modifiers:
                pressed_keys.add(kb_key)
            elif hasattr(kb_key, "char") and kb_key.char == key:
                if modifiers.issubset(pressed_keys):
                    asyncio.run_coroutine_threadsafe(process_screenshot(), _loop)
        except (AttributeError, TypeError):
            pass

    def on_release(kb_key):
        try:
            pressed_keys.discard(kb_key)
        except (AttributeError, TypeError):
            pass

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()


def main() -> None:
    """Start floating button and async event loop."""
    global _loop, _loop_thread, _floating_button

    if sys.platform != "win32":
        print("❌ This app is Windows-only.")
        sys.exit(1)

    print("GeoGuessr Helper started")
    print(f"✓ Floating button in top-left corner")
    print(f"✓ Also works with hotkey: {HOTKEY}\n")

    # Start event loop in background thread
    _loop = asyncio.new_event_loop()
    _loop_thread = threading.Thread(target=run_event_loop, args=(_loop,), daemon=True)
    _loop_thread.start()

    # Start floating button
    def button_callback():
        asyncio.run_coroutine_threadsafe(process_screenshot(), _loop)

    _floating_button = FloatingButton(button_callback)
    _floating_button.start()

    # Also setup hotkey as backup
    try:
        setup_hotkey_listener_windows()
    except Exception as e:
        print(f"⚠ Hotkey setup failed: {e}")

    try:
        # Keep main thread alive
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\nExiting...")
        if _floating_button:
            _floating_button.destroy()
        _loop.call_soon_threadsafe(_loop.stop)
        sys.exit(0)


if __name__ == "__main__":
    main()
