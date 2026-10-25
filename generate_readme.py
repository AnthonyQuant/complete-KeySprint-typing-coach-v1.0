"""Automated script to generate portfolio-ready README.md for KeySprint."""

import os

README_CONTENT = """# KeySprint — Personal Typing Coach & Developer Performance Studio

KeySprint is a modular, high-performance desktop application built in Python that goes beyond standard typing speed tests. Designed specifically for developers and technical typists, KeySprint combines real-time character matching, localized analytics, custom code snippet practice, and an automated **Weakness Analyzer** to systematically eliminate typing friction.

---

## 🌟 Key Features

* **⚡ Real-Time Character Feedback**: Character-by-character visual feedback (untyped, correct, incorrect, active cursor) with instant accuracy and WPM calculations.
* **💻 Developer Mode**: Train on authentic Python code snippets containing brackets `() [] {}`, operators `+=, ==`, indentation, and underscores `_`.
* **🧠 Signature Feature: Personal Weakness Analyzer**: Automatically tracks keypress error frequencies in an offline SQLite database and dynamically generates targeted practice drills targeting your specific weak keys.
* **📈 Visual Analytics & Progress Tracking**: Embedded dark-themed `matplotlib` trend charts mapping WPM progression and overall accuracy across historical test attempts.
* **🏆 Local Achievement & Goal System**: Track and unlock local milestone badges (e.g., *Speed Demon*, *Flawless Code*, *Ironclad*) stored locally without external web dependencies.
* **🎲 Dynamic Word Stream Generator**: Monkeytype-style dynamic word sampling and passage shuffling ensuring zero repetitive tests.

---

## 📐 Mathematical Metrics & Formulas

### 1. Gross Words Per Minute (WPM)
KeySprint uses the standardized 5-character word metric:

$$\\text{WPM} = \\frac{\\text{Total Characters Typed} / 5.0}{\\text{Elapsed Time in Minutes}}$$

### 2. Typing Accuracy Percentage

$$\\text{Accuracy} = \\left( \\frac{\\text{Correctly Typed Characters}}{\\text{Total Typed Characters}} \\right) \\times 100$$

### 3. Keystroke Weakness Matrix
For every miskeyed character, KeySprint updates an expected-to-typed error matrix:

$$\\text{Error Count}(C_{\\text{expected}}, C_{\\text{typed}}) = \\sum_{s \\in S} \\text{occurrences}$$

The top mistyped characters are extracted via SQL `GROUP BY` aggregations to build custom practice streams.

---

## 🏗️ System Architecture & Modular Design

```text
KeySprint/
├── data/
│   ├── passages.json          # Vocabulary pools & Python code snippet templates
│   └── history.db             # Local SQLite database (sessions & character errors)
├── src/
│   ├── engine.py              # Pure-logic core: timers, keystroke state, WPM/Accuracy
│   ├── passages.py            # Dynamic passage generator & weakness exercise builder
│   ├── analytics.py           # SQLite persistence, aggregate stats & error matrix
│   ├── achievements.py        # Local challenge evaluation & badge criteria
│   └── ui.py                  # Graphical User Interface (Tkinter & Matplotlib)
├── tests/
│   ├── test_engine.py         # WPM/Accuracy formula & state transition unit tests
│   ├── test_passages.py       # Vocabulary loading & drill generator tests
│   ├── test_analytics.py      # SQLite logging & weakness count tests
│   ├── test_achievements.py   # Badge unlocking evaluation tests
│   └── test_edge_cases.py     # Boundary testing (zero time, backspacing at index 0)
├── pytest.ini                 # Pytest runner configuration
├── run_tests.py               # Automated test execution script
├── main.py                    # Main application launcher
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation 
"""