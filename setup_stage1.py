import os

# Project layout definition
DIRECTORIES = [
    "data",
    "src",
    "tests",
]

FILES = {
    "requirements.txt": "customtkinter>=5.2.0\nmatplotlib>=3.7.0\npytest>=7.0.0\n",
    ".gitignore": "__pycache__/\n*.pyc\n*.db\n.venv/\n.pytest_cache/\n",
    "src/__init__.py": "",
    "src/engine.py": '"""Core typing mechanics, state management, and real-time metric calculations."""\n',
    "src/passages.py": '"""Passage management, category filtering, and Developer Mode snippet loader."""\n',
    "src/analytics.py": '"""SQLite data persistence, historical performance analysis, and Weakness Analyzer."""\n',
    "src/achievements.py": '"""Local challenge and achievement criteria tracking."""\n',
    "src/ui.py": '"""Tkinter/CustomTkinter Graphical Interface."""\n',
    "tests/__init__.py": "",
    "tests/test_engine.py": '"""Unit tests for engine metrics and timer transitions."""\n',
    "tests/test_analytics.py": '"""Unit tests for weakness frequency counts and data persistence."""\n',
    "main.py": '''"""Application Entry Point for Personal Typing Coach."""
import sys
import os

# Add src directory to system path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

def main():
    print("=== Personal Typing Coach Initialized ===")
    print("Stage 1 scaffold ready. Run Stage 2 to implement engine calculations.")

if __name__ == "__main__":
    main()
''',
    "README.md": "# Personal Typing Coach\n\nAn intelligent desktop typing test and weakness analyzer built with Python."
}


def create_scaffold():
    print("=== Stage 1: Initializing Project Architecture ===")

    # 1. Create directories
    for directory in DIRECTORIES:
        os.makedirs(directory, exist_ok=True)
        print(f"[Directory Created] ./{directory}/")

    # 2. Create placeholder files
    for file_path, content in FILES.items():
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[File Created] ./{file_path}")
        else:
            print(f"[File Exists] ./{file_path}")

    print("\nStage 1 Architecture Setup Complete!")


if __name__ == "__main__":
    create_scaffold()