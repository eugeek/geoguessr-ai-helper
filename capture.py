import mss
from PIL import Image
from io import BytesIO


def capture_screen() -> bytes:
    """Capture full screen and crop out GeoGuessr UI elements."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        width = monitor["width"]
        height = monitor["height"]

        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        # Crop: remove edges to avoid UI (minimap, score, timer)
        # left+5%, top+8%, right-5%, bottom-12%
        left = int(width * 0.05)
        top = int(height * 0.08)
        right = int(width * 0.95)
        bottom = int(height * 0.88)

        cropped = img.crop((left, top, right, bottom))

        # Convert to PNG bytes
        buffer = BytesIO()
        cropped.save(buffer, format="PNG")
        return buffer.getvalue()
