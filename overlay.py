import threading
import tkinter as tk
from tkinter import Label, Frame
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import sys
from analyzer import GeoResult

_overlay_window = None
_last_screenshot = None


def set_last_screenshot(image_bytes):
    """Store last screenshot for display."""
    global _last_screenshot
    _last_screenshot = image_bytes


def show_result(result: GeoResult) -> None:
    """Display overlay with map marker, result, and screenshot."""
    if sys.platform != "win32":
        return

    global _overlay_window

    def create_overlay():
        global _overlay_window

        # Close existing window
        if _overlay_window and _overlay_window.winfo_exists():
            _overlay_window.destroy()

        _overlay_window = tk.Tk()
        _overlay_window.title(f"{result.country} · {result.confidence}%")
        _overlay_window.geometry("700x600")
        _overlay_window.attributes("-topmost", True)
        _overlay_window.attributes("-toolwindow", True)
        _overlay_window.configure(bg="#1a1a1a")

        # Position bottom-right
        _overlay_window.update_idletasks()
        screen_width = _overlay_window.winfo_screenwidth()
        screen_height = _overlay_window.winfo_screenheight()
        x = screen_width - 720
        y = screen_height - 620
        _overlay_window.geometry(f"700x600+{x}+{y}")

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
                # Resize for preview (max 300x200)
                img.thumbnail((300, 200), Image.Resampling.LANCZOS)
                screenshot_tk = tk.PhotoImage(image=img)

                screenshot_label = Label(
                    content,
                    image=screenshot_tk,
                    bg="#2a2a2a",
                    bd=2,
                    relief="sunken",
                )
                screenshot_label.image = screenshot_tk
                screenshot_label.pack(pady=5)
            except Exception as e:
                error_label = Label(
                    content,
                    text=f"[Screenshot preview error: {str(e)[:30]}]",
                    font=("Arial", 8),
                    bg="#2a2a2a",
                    fg="#e74c3c",
                )
                error_label.pack(pady=5)

        # Map info with marker
        map_frame = Frame(content, bg="#34495e", relief="sunken", bd=1)
        map_frame.pack(fill="both", expand=True, pady=5)

        map_label = Label(
            map_frame,
            text=f"📍 Map: {result.lat:.6f}, {result.lon:.6f}",
            font=("Arial", 11, "bold"),
            bg="#34495e",
            fg="#ecf0f1",
            pady=20,
        )
        map_label.pack()

        # Analysis text
        analysis_frame = Frame(content, bg="#2a2a2a", relief="sunken", bd=1)
        analysis_frame.pack(fill="x", pady=5)

        analysis_label = Label(
            analysis_frame,
            text=result.explanation,
            font=("Arial", 9),
            bg="#2a2a2a",
            fg="#bdc3c7",
            wraplength=660,
            justify="left",
            padx=10,
            pady=8,
        )
        analysis_label.pack(fill="both")

        # Footer with timestamp
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
