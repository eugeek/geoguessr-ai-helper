import threading
import tkinter as tk
from tkinter import Label, Frame, Button
from PIL import Image, ImageTk
from io import BytesIO
import sys
import urllib.request
import logging
from analyzer import GeoResult

logger = logging.getLogger(__name__)

_overlay_window = None
_last_screenshot = None


def set_last_screenshot(image_bytes):
    """Store last screenshot for display."""
    global _last_screenshot
    _last_screenshot = image_bytes


def fetch_static_map(lat: float, lon: float, zoom: int = 13) -> bytes:
    """Fetch OpenStreetMap static map image with marker."""
    try:
        static_url = (
            f"https://staticmap.openstreetmap.de/staticmap.php"
            f"?center={lat},{lon}&zoom={zoom}"
            f"&size=400x300&maptype=mapnik"
            f"&markers={lat},{lon},lightblue"
        )

        req = urllib.request.Request(static_url, headers={"User-Agent": "GeoGuessr-Helper/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.read()
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

        def update_map(zoom_delta):
            zoom_state["zoom"] = max(2, min(18, zoom_state["zoom"] + zoom_delta))
            zoom_label.config(text=f"Zoom: {zoom_state['zoom']}")

            map_img_bytes = fetch_static_map(result.lat, result.lon, zoom=zoom_state["zoom"])
            if map_img_bytes:
                try:
                    map_img = Image.open(BytesIO(map_img_bytes))
                    map_photo = ImageTk.PhotoImage(map_img)
                    map_display.config(image=map_photo)
                    map_display.image = map_photo
                except Exception as e:
                    logger.error(f"Map update error: {e}")

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

        # Map image
        map_img_bytes = fetch_static_map(result.lat, result.lon, zoom=zoom_state["zoom"])
        if map_img_bytes:
            try:
                map_img = Image.open(BytesIO(map_img_bytes))
                map_photo = ImageTk.PhotoImage(map_img)

                map_frame = Frame(map_container, bg="#2a2a2a", relief="sunken", bd=2)
                map_frame.pack(fill="both", expand=True, pady=2)

                map_display = Label(
                    map_frame,
                    image=map_photo,
                    bg="#2a2a2a",
                )
                map_display.image = map_photo
                map_display.pack(padx=5, pady=5)
            except Exception as e:
                logger.error(f"Map rendering error: {e}")
                map_error = Label(
                    map_container,
                    text="🗺️ Map failed to load",
                    font=("Arial", 10),
                    bg="#34495e",
                    fg="#e74c3c",
                )
                map_error.pack(fill="both", expand=True)
        else:
            map_error = Label(
                map_container,
                text="🗺️ Could not load map",
                font=("Arial", 10),
                bg="#34495e",
                fg="#e74c3c",
                pady=40,
            )
            map_error.pack(fill="both", expand=True, pady=2)

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
