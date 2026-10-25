"""Application Entry Point for KeySprint Personal Typing Coach."""

import os
import sys
import tkinter as tk

# Ensure 'src' directory is in Python module path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from ui import TypingCoachApp


def main():
    root = tk.Tk()
    app = TypingCoachApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()