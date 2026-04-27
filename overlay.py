import threading
import tkinter as tk
from tkinter import Label, Frame, Button
from PIL import Image
from io import BytesIO
import sys
import urllib.request
import logging
from analyzer import GeoResult
import tempfile
import os

logger = logging.getLogger(__name__)

_overlay_window = None
_last_screenshot = None


def set_last_screenshot(image_bytes):
    """Store last screenshot for display."""
    global _last_screenshot
    _last_screenshot = image_bytes


def _deg2tile(lat: float, lon: float, zoom: int):
    import math
    n = 2 ** zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def fetch_static_map(lat: float, lon: float, zoom: int = 13) -> bytes:
    """Fetch map by stitching OSM tiles into a 3x3 grid."""
    try:
        from PIL import Image as PILImage
        from io import BytesIO

        cx, cy = _deg2tile(lat, lon, zoom)
        tile_size = 256
        grid = 3
        result = PILImage.new("RGB", (tile_size * grid, tile_size * grid))

        for dx in range(grid):
            for dy in range(grid):
                tx, ty = cx - 1 + dx, cy - 1 + dy
                url = f"https://tile.openstreetmap.org/{zoom}/{tx}/{ty}.png"
                req = urllib.request.Request(url, headers={"User-Agent": "GeoGuessr-Helper/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    tile = PILImage.open(BytesIO(resp.read())).convert("RGB")
                result.paste(tile, (dx * tile_size, dy * tile_size))

        # Draw marker dot
        from PIL import ImageDraw
        draw = ImageDraw.Draw(result)
        center = (tile_size * grid // 2, tile_size * grid // 2)
        r = 8
        draw.ellipse([center[0]-r, center[1]-r, center[0]+r, center[1]+r], fill="red", outline="white", width=2)

        buf = BytesIO()
        result.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Failed to fetch map image: {e}")
        return None


def show_result(result: GeoResult) -> None:
    """Display result in overlay window with map."""
    if sys.platform != "win32":
        return

    global _overlay_window

    def create_overlay():
        global _overlay_window

        if _overlay_window and _overlay_window.winfo_exists():
            _overlay_window.destroy()

        _overlay_window = tk.Tk()
        _overlay_window.title(f"{result.country} · {result.confidence}%")
        _overlay_window.geometry("800x700")
        _overlay_window.attributes("-topmost", True)
        _overlay_window.attributes("-toolwindow", True)
        _overlay_window.configure(bg="#1a1a1a")

        _overlay_window.update_idletasks()
        screen_width = _overlay_window.winfo_screenwidth()
        screen_height = _overlay_window.winfo_screenheight()
        x = screen_width - 820
        y = screen_height - 720
        _overlay_window.geometry(f"800x700+{x}+{y}")

        # Header
        header = Frame(_overlay_window, bg="#2c3e50", height=50)
        header.pack(fill="x")

        title = Label(
            header,
            text=f"📍 {result.country} · {result.confidence}%",
            font=("Arial", 14, "bold"),
            bg="#2c3e50",
            fg="white",
        )
        title.pack(side="left", padx=15, pady=10)

        coords = Label(
            header,
            text=f"{result.lat:.4f}, {result.lon:.4f}",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="#bdc3c7",
        )
        coords.pack(side="right", padx=15, pady=10)

        # Main content
        content = Frame(_overlay_window, bg="#1a1a1a")
        content.pack(fill="both", expand=True, padx=10, pady=10)

        # Map frame with zoom controls
        map_container = Frame(content, bg="#1a1a1a")
        map_container.pack(fill="both", expand=True, pady=5)

        # Zoom controls
        zoom_controls = Frame(map_container, bg="#1a1a1a")
        zoom_controls.pack(fill="x", padx=5, pady=3)

        zoom_state = {"zoom": 13}

        zoom_label = Label(
            zoom_controls,
            text=f"Zoom: {zoom_state['zoom']}",
            font=("Arial", 8),
            bg="#1a1a1a",
            fg="#7f8c8d",
        )
        zoom_label.pack(side="left")

        btn_zoom_in = Button(
            zoom_controls,
            text="+ Zoom In",
            command=lambda: update_map(1),
            bg="#34495e",
            fg="white",
            font=("Arial", 8),
            padx=8,
            pady=2,
        )
        btn_zoom_in.pack(side="right", padx=2)

        btn_zoom_out = Button(
            zoom_controls,
            text="- Zoom Out",
            command=lambda: update_map(-1),
            bg="#34495e",
            fg="white",
            font=("Arial", 8),
            padx=8,
            pady=2,
        )
        btn_zoom_out.pack(side="right", padx=2)

        map_frame = Frame(map_container, bg="#2a2a2a", relief="sunken", bd=2)
        map_frame.pack(fill="both", expand=True, pady=2)

        map_display = Label(map_frame, bg="#2a2a2a", text="Loading map...", fg="#7f8c8d")
        map_display.pack(fill="both", expand=True)

        map_tmp = os.path.join(tempfile.gettempdir(), "geoguessr_map_tile.ppm")

        def load_map(zoom):
            map_img_bytes = fetch_static_map(result.lat, result.lon, zoom=zoom)
            if map_img_bytes:
                try:
                    img = Image.open(BytesIO(map_img_bytes))
                    img.convert("RGB").save(map_tmp, format="PPM")
                    photo = tk.PhotoImage(file=map_tmp)
                    map_display.config(image=photo, text="")
                    map_display.image = photo
                except Exception as e:
                    logger.error(f"Map rendering error: {e}")
                    map_display.config(text="🗺️ Map failed to load", image="")

        def update_map(zoom_delta):
            zoom_state["zoom"] = max(2, min(18, zoom_state["zoom"] + zoom_delta))
            zoom_label.config(text=f"Zoom: {zoom_state['zoom']}")
            _overlay_window.after(0, lambda: load_map(zoom_state["zoom"]))

        _overlay_window.after(0, lambda: load_map(zoom_state["zoom"]))

        # Analysis text
        analysis_frame = Frame(content, bg="#2a2a2a", relief="sunken", bd=1)
        analysis_frame.pack(fill="x", pady=5)

        analysis_label = Label(
            analysis_frame,
            text=result.explanation,
            font=("Arial", 8),
            bg="#2a2a2a",
            fg="#bdc3c7",
            wraplength=770,
            justify="left",
            padx=8,
            pady=6,
        )
        analysis_label.pack(fill="both")

        # Footer
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        footer = Frame(_overlay_window, bg="#1a1a1a")
        footer.pack(fill="x", padx=10, pady=5)

        footer_label = Label(
            footer,
            text=f"✓ Analysis complete at {timestamp}",
            font=("Arial", 8),
            bg="#1a1a1a",
            fg="#7f8c8d",
        )
        footer_label.pack(side="left")

        _overlay_window.mainloop()

    thread = threading.Thread(target=create_overlay, daemon=True)
    thread.start()
