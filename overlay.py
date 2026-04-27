import threading
import tkinter as tk
from tkinter import Label, Frame
from PIL import Image, ImageTk
from io import BytesIO
import sys
import logging
import folium
import tempfile
import os
from analyzer import GeoResult

logger = logging.getLogger(__name__)

_overlay_window = None
_last_screenshot = None

try:
    from tkinterweb import HtmlFrame
    HAS_TKINTERWEB = True
except ImportError:
    HAS_TKINTERWEB = False


def set_last_screenshot(image_bytes):
    """Store last screenshot for display."""
    global _last_screenshot
    _last_screenshot = image_bytes


def create_interactive_map(lat: float, lon: float) -> str:
    """Create interactive Folium map and return HTML file path."""
    try:
        m = folium.Map(
            location=[lat, lon],
            zoom_start=13,
            tiles="OpenStreetMap",
        )

        folium.Marker(
            location=[lat, lon],
            popup=f"📍 {lat:.6f}, {lon:.6f}",
            icon=folium.Icon(color="red", icon="location-dot"),
        ).add_to(m)

        temp_dir = tempfile.gettempdir()
        map_file = os.path.join(temp_dir, "geoguessr_map.html")
        m.save(map_file)
        return map_file
    except Exception as e:
        logger.error(f"Failed to create map: {e}")
        return None


def show_result(result: GeoResult, button_window=None) -> None:
    """Display result in overlay window with interactive map."""
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

        # Screenshot preview
        if _last_screenshot:
            try:
                img = Image.open(BytesIO(_last_screenshot))
                img.thumbnail((350, 180), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                screenshot_frame = Frame(content, bg="#2a2a2a", relief="sunken", bd=1)
                screenshot_frame.pack(pady=5)

                screenshot_label = Label(
                    screenshot_frame,
                    image=photo,
                    bg="#2a2a2a",
                )
                screenshot_label.image = photo
                screenshot_label.pack(padx=5, pady=5)
            except Exception as e:
                logger.warning(f"Screenshot preview error: {e}")

        # Map frame
        map_container = Frame(content, bg="#2a2a2a", relief="sunken", bd=2)
        map_container.pack(fill="both", expand=True, pady=5)

        # Create map
        map_file = create_interactive_map(result.lat, result.lon)
        if map_file and HAS_TKINTERWEB:
            try:
                html_frame = HtmlFrame(map_container, horizontal_scrollbar="auto")
                html_frame.load_file(map_file)
                html_frame.pack(fill="both", expand=True)
            except Exception as e:
                logger.error(f"Map embed error: {e}")
                map_label = Label(
                    map_container,
                    text=f"🗺️ Map coordinates:\n{result.lat:.6f}, {result.lon:.6f}",
                    font=("Arial", 11),
                    bg="#2a2a2a",
                    fg="#bdc3c7",
                    justify="center",
                )
                map_label.pack(fill="both", expand=True)
        else:
            map_label = Label(
                map_container,
                text=f"🗺️ Map coordinates:\n{result.lat:.6f}, {result.lon:.6f}",
                font=("Arial", 11),
                bg="#2a2a2a",
                fg="#bdc3c7",
                justify="center",
            )
            map_label.pack(fill="both", expand=True)

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
