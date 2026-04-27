import tkinter as tk
from tkinter import simpledialog, messagebox
import os


def setup_api_key():
    """Show setup dialog if API key is missing."""
    env_file = ".env"

    # Check if .env exists and has API key
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            content = f.read()
            if "GEMINI_API_KEY=" in content and not content.split("GEMINI_API_KEY=")[1].startswith("your_"):
                return  # Key already set

    # Show setup dialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    # API Key input
    api_key = simpledialog.askstring(
        "GeoGuessr Helper - Setup",
        "Enter your Gemini API Key:\n\n"
        "Get it from: https://aistudio.google.com/apikey\n\n"
        "API Key:",
        show="*",
    )

    if not api_key:
        messagebox.showerror("Error", "API Key is required to run the app")
        root.destroy()
        return False

    # Hotkey input (optional)
    hotkey = simpledialog.askstring(
        "GeoGuessr Helper - Setup",
        "Enter hotkey (default: ctrl+alt+g)\n\n"
        "Format: ctrl+alt+g, shift+f12, etc.\n\n"
        "Leave empty for default:",
    )

    if not hotkey:
        hotkey = "ctrl+alt+g"

    # Save to .env
    env_content = f"GEMINI_API_KEY={api_key}\nHOTKEY={hotkey}\n"

    with open(env_file, "w") as f:
        f.write(env_content)

    messagebox.showinfo("Success", "Setup complete! App will start now.")
    root.destroy()
    return True
