"""Unit tests for typing engine formulas, state transitions, and edge cases."""

import os
import sys
import time
import pytest

# Dynamically add the 'src' directory to Python's module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from engine import TypingEngine, EngineState


def test_initial_state():
    engine = TypingEngine("Hello world", duration_seconds=60)
    assert engine.state == EngineState.IDLE
    assert engine.calculate_wpm() == 0.0
    assert engine.calculate_accuracy() == 100.0


def test_first_keystroke_starts_timer():
    engine = TypingEngine("Hello world")
    engine.process_key("H")
    assert engine.state == EngineState.RUNNING
    assert engine.get_elapsed_seconds() >= 0.0


def test_wpm_calculation():
    engine = TypingEngine("Hello world, this is a test passage.")
    engine.start_test()
    engine.start_time = time.time() - 60  # Mock 60 seconds elapsed

    # 30 characters typed in 1 minute = (30 / 5) / 1 = 6 WPM
    for char in "Hello world, this is a test pa":
        engine.typed_text += char

    assert engine.calculate_wpm() == 6.0


def test_accuracy_calculation():
    engine = TypingEngine("python")
    # Type 'pythxx' (4 correct, 2 incorrect)
    for c in "pythxx":
        engine.process_key(c)

    assert engine.calculate_accuracy() == 66.67


def test_backspace_handling():
    engine = TypingEngine("python")
    engine.process_key("p")
    engine.process_key("x")
    assert engine.typed_text == "px"

    engine.process_backspace()
    assert engine.typed_text == "p"
    assert engine.calculate_accuracy() == 100.0