import tkinter as tk
import threading
from config import HOTKEY


class FloatingButton:
    """Floating button always on top of all windows."""

    def __init__(self, callback):
        self.callback = callback
        self.window = None
        self.thread = None

    def start(self):
        """Start floating button in background thread."""
        self.thread = threading.Thread(target=self._create_window, daemon=True)
        self.thread.start()

    def _create_window(self):
        """Create transparent floating button window."""
        self.window = tk.Tk()
        self.window.title("GeoGuessr")
        self.window.geometry("60x60+50+50")
        self.window.attributes("-topmost", True)
        self.window.attributes("-toolwindow", True)

        # Make window transparent except button
        button = tk.Button(
            self.window,
            text="📍\nAnalyze",
            command=self.callback,
            bg="#2c3e50",
            fg="white",
            font=("Arial", 8, "bold"),
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=5,
            pady=5,
        )
        button.pack(fill="both", expand=True)

        # Position in top-left corner
        self.window.geometry("70x70+20+20")

        self.window.mainloop()

    def destroy(self):
        """Close button window."""
        if self.window:
            self.window.destroy()
