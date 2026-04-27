import threading
import webbrowser
import sys
from analyzer import GeoResult

_overlay_thread = None
_overlay_window = None

# Platform-specific imports
if sys.platform == "win32":
    import tkinter as tk
    from tkinter import Label, Frame
else:
    import tkinter as tk
    from tkinter import Label, Frame


def show_result(result: GeoResult) -> None:
    """Display floating overlay with Google Maps marker and location info."""
    global _overlay_thread, _overlay_window

    maps_url = f"https://www.google.com/maps/@{result.lat},{result.lon},15z?markers={result.lat},{result.lon}"

    def create_overlay():
        global _overlay_window

        # Close existing window
        if _overlay_window and _overlay_window.winfo_exists():
            _overlay_window.destroy()

        _overlay_window = tk.Tk()
        _overlay_window.title(f"{result.country} · {result.confidence}%")
        _overlay_window.geometry("600x400")
        _overlay_window.attributes("-topmost", True)

        # Set window style (Windows: minimize button only, always on top)
        if sys.platform == "win32":
            _overlay_window.attributes("-toolwindow", True)

        # Position in bottom-right
        _overlay_window.update_idletasks()
        screen_width = _overlay_window.winfo_screenwidth()
        screen_height = _overlay_window.winfo_screenheight()
        x = screen_width - 620
        y = screen_height - 420
        _overlay_window.geometry(f"600x400+{x}+{y}")

        # Main frame
        main_frame = Frame(_overlay_window, bg="#ffffff")
        main_frame.pack(fill="both", expand=True)

        # Title section
        title_frame = Frame(main_frame, bg="#2c3e50", height=40)
        title_frame.pack(fill="x")

        title_label = Label(
            title_frame,
            text=f"{result.country} · {result.confidence}%",
            font=("Arial", 12, "bold"),
            bg="#2c3e50",
            fg="white",
        )
        title_label.pack(anchor="w", padx=12, pady=8)

        # Map area (opens Maps in browser on click)
        map_frame = Frame(main_frame, bg="#ecf0f1", height=250)
        map_frame.pack(fill="both", expand=True, padx=10, pady=10)

        map_info = Label(
            map_frame,
            text=f"📍 {result.lat:.4f}, {result.lon:.4f}\n\nClick here to open in Google Maps",
            font=("Arial", 11),
            bg="#ecf0f1",
            fg="#34495e",
            cursor="hand2",
        )
        map_info.pack(fill="both", expand=True)

        def open_maps(event=None):
            webbrowser.open(maps_url)

        map_info.bind("<Button-1>", open_maps)

        # Info section
        info_frame = Frame(main_frame, bg="#f8f9fa")
        info_frame.pack(fill="x", padx=10, pady=10)

        explanation_label = Label(
            info_frame,
            text=f"Analysis: {result.explanation}",
            font=("Arial", 9),
            bg="#f8f9fa",
            fg="#555555",
            wraplength=570,
            justify="left",
        )
        explanation_label.pack(anchor="w", pady=5)

        coords_label = Label(
            info_frame,
            text=f"Coordinates: {result.lat:.6f}, {result.lon:.6f}",
            font=("Arial", 8),
            bg="#f8f9fa",
            fg="#888888",
        )
        coords_label.pack(anchor="w")

        # Auto-open Maps in background
        webbrowser.open(maps_url)

        _overlay_window.mainloop()

    _overlay_thread = threading.Thread(target=create_overlay, daemon=True)
    _overlay_thread.start()
