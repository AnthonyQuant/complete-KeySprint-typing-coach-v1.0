"""Application Entry Point for KeySprint Personal Typing Coach."""

import os
import sys
import tkinter as tk

# Ensure project root directory is in Python module search path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui import TypingCoachApp


def main():
    # Enable High-DPI awareness on Windows for crisp rendering
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    app = TypingCoachApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()