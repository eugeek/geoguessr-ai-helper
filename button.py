import tkinter as tk
import threading
from config import HOTKEY


class FloatingButton:
    """Floating button that expands to show results."""

    def __init__(self, callback):
        self.callback = callback
        self.window = None
        self.thread = None
        self.button = None
        self.is_loading = False
        self.is_expanded = False

    def start(self):
        """Start floating button in background thread."""
        self.thread = threading.Thread(target=self._create_window, daemon=True)
        self.thread.start()

    def set_loading(self, loading: bool):
        """Show/hide loading spinner on button."""
        self.is_loading = loading
        if self.button and not self.is_expanded:
            if loading:
                self.button.config(state="disabled", text="⏳\nLoading...", bg="#7f8c8d")
            else:
                self.button.config(state="normal", text="📍\nAnalyze", bg="#2c3e50")

    def set_expanded(self, expanded: bool, result=None):
        """Expand/collapse button to show results."""
        self.is_expanded = expanded
        if expanded and self.window and result:
            self.window.geometry("800x700")
            self.button.pack_forget()
        elif not expanded and self.window:
            self.window.geometry("70x70")
            self.button.pack(fill="both", expand=True)

    def _on_click(self):
        """Handle button click with loading state."""
        if not self.is_expanded:
            self.set_loading(True)
            self.window.after(100, self._execute_callback)

    def _execute_callback(self):
        """Execute callback in background thread."""
        def run():
            try:
                self.callback()
            finally:
                pass

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _create_window(self):
        """Create floating button window."""
        self.window = tk.Tk()
        self.window.title("GeoGuessr Helper")
        self.window.geometry("70x70+20+20")
        self.window.attributes("-topmost", True)
        self.window.attributes("-toolwindow", True)
        self.window.configure(bg="#1a1a1a")

        # Button
        self.button = tk.Button(
            self.window,
            text="📍\nAnalyze",
            command=self._on_click,
            bg="#2c3e50",
            fg="white",
            font=("Arial", 8, "bold"),
            relief="raised",
            bd=2,
            cursor="hand2",
            padx=5,
            pady=5,
            activebackground="#34495e",
            activeforeground="white",
        )
        self.button.pack(fill="both", expand=True)

        self.window.mainloop()

    def destroy(self):
        """Close button window."""
        if self.window:
            self.window.destroy()
