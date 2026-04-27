import asyncio
import threading
import sys
from config import HOTKEY
from capture import capture_screen
from analyzer import analyze
from overlay import show_result

_loop = None
_loop_thread = None
_processing = False

# Platform-specific hotkey setup
if sys.platform == "win32":
    import win32con
    import win32api
    from pynput import keyboard
else:
    from pynput import keyboard


async def process_screenshot() -> None:
    """Capture, analyze, and display result."""
    global _processing

    if _processing:
        return

    _processing = True

    try:
        print("[►] Capturing...")
        image_bytes = capture_screen()

        print("[◌] Analyzing...")
        result = await analyze(image_bytes)

        print(f"[✓] {result.country} (confidence: {result.confidence}%)")
        show_result(result)

    except Exception as e:
        print(f"[✗] Error: {e}")
    finally:
        _processing = False


def run_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Run asyncio event loop in background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def parse_hotkey(hotkey_str: str) -> tuple:
    """Parse 'ctrl+alt+g' to pynput format."""
    parts = hotkey_str.lower().split("+")
    modifiers = set()
    key = None

    modifier_map = {
        "ctrl": keyboard.Key.ctrl,
        "alt": keyboard.Key.alt,
        "shift": keyboard.Key.shift,
        "cmd": keyboard.Key.cmd,
        "option": keyboard.Key.alt,
    }

    for part in parts:
        if part in modifier_map:
            modifiers.add(modifier_map[part])
        else:
            key = part

    return modifiers, key


def setup_hotkey_listener() -> None:
    """Setup global hotkey listener using pynput."""
    required_modifiers, required_key = parse_hotkey(HOTKEY)
    pressed_keys = set()

    def on_press(key):
        try:
            if key in required_modifiers:
                pressed_keys.add(key)
            elif hasattr(key, "char") and key.char == required_key:
                if required_modifiers.issubset(pressed_keys):
                    asyncio.run_coroutine_threadsafe(process_screenshot(), _loop)
        except (AttributeError, TypeError):
            pass

    def on_release(key):
        try:
            pressed_keys.discard(key)
        except (AttributeError, TypeError):
            pass

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()


def main() -> None:
    """Start hotkey listener and async event loop."""
    global _loop, _loop_thread

    print(f"GeoGuessr Helper started. Press {HOTKEY} to analyze.")
    if sys.platform == "win32":
        print("⚠ Windows: Admin rights recommended for reliable hotkey detection")
    print("Press Ctrl+C to exit.\n")

    # Start event loop in background thread
    _loop = asyncio.new_event_loop()
    _loop_thread = threading.Thread(target=run_event_loop, args=(_loop,), daemon=True)
    _loop_thread.start()

    # Setup hotkey listener
    try:
        setup_hotkey_listener()
    except Exception as e:
        print(f"⚠ Hotkey setup failed: {e}\n")

    try:
        # Keep main thread alive
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\nExiting...")
        _loop.call_soon_threadsafe(_loop.stop)
        sys.exit(0)


if __name__ == "__main__":
    main()
