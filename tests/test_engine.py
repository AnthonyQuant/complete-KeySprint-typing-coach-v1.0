"""Unit tests for TypingEngine engine form, state transitions, and edge cases."""

import os
import sys
import time
import pytest

# Dynamically add the 'src' directory to Python's module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from engine import TypingEngine, EngineState


def test_initial_state():
    engine = TypingEngine("Hello world", duration_seconds=60)
    assert engine.target_text == "Hello world"
    assert engine.state == EngineState.IDLE
    assert engine.calculate_wpm() == 0.0
    assert engine.calculate_accuracy() == 100.0


def test_first_keystroke_starts_timer():
    engine = TypingEngine("Hello world")
    engine.process_key("H")
    assert engine.state == EngineState.RUNNING
    # Verify the clock started without relying on execution delays
    assert engine.start_time > 0.0


def test_wpm_calculation():
    engine = TypingEngine("Hello world, this is a test passage.")
    engine.start_test()

    for char in "Hello world, this is a test pa":
        engine.process_key(char)

    # Mock 60 seconds elapsed time and transition to FINISHED
    engine.start_time = 0.0
    engine.end_time = 60.0
    engine.state = EngineState.FINISHED

    # 30 correct characters / 5 = 6 words in 1 minute = 6.0 WPM
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
    engine.process_key("y")
    engine.process_key("x")
    assert engine.typed_text == "pyx"

    engine.process_backspace()
    assert engine.typed_text == "py"


def test_monotonic_timer_and_observational_getters():
    """Verify timing uses monotonic clocks and get_elapsed_seconds does not mutate state."""
    engine = TypingEngine("test_python", duration_seconds=60)
    assert engine.get_elapsed_seconds() == 0.0

    engine.start_test()
    assert engine.state == EngineState.RUNNING
    time.sleep(0.03)

    elapsed1 = engine.get_elapsed_seconds()
    assert elapsed1 > 0.0

    elapsed2 = engine.get_elapsed_seconds()  # Getter does not mutate state
    assert elapsed2 >= elapsed1
    assert engine.state == EngineState.RUNNING

    engine.finish_test()
    assert engine.state == EngineState.FINISHED
    elapsed3 = engine.get_elapsed_seconds()
    time.sleep(0.02)
    assert engine.get_elapsed_seconds() == elapsed3  # Elapsed time remains fixed once finished


def test_dual_accuracy_metrics_with_backspace():
    """Verify difference between final-text accuracy and keystroke accuracy after correction."""
    target = "py"
    engine = TypingEngine(target)

    # Type 'p', type wrong key 'x', press backspace, then type correct key 'y'
    engine.process_key("p")
    engine.process_key("x")  # Typo on 'y'
    engine.process_backspace()
    engine.process_key("y")  # Correction

    assert engine.typed_text == "py"
    assert engine.total_keystrokes == 3
    assert engine.calculate_final_accuracy() == 100.0
    assert engine.calculate_keystroke_accuracy() == 66.67  # 2 correct attempts out of 3 keystrokes


def test_gross_vs_net_wpm():
    """Verify gross WPM counts all keystrokes while net WPM counts remaining correct characters."""
    # Changed target from "hello" to "helloworld" so the engine accepts all 10 keystrokes
    target = "helloworld"
    engine = TypingEngine(target)
    engine.start_test()

    # Simulate 10 actual character entry attempts
    for _ in range(10):
        engine.process_key("x")
    # Backspace them all to leave an empty final buffer
    for _ in range(10):
        engine.process_backspace()

    # Manually simulate 60 seconds elapsed for simple math
    engine.start_time = 0.0
    engine.end_time = 60.0
    engine.state = EngineState.FINISHED

    assert engine.calculate_gross_wpm() == 2.0  # 10 keystrokes / 5 / 1 minute = 2.0 WPM
    assert engine.calculate_net_wpm() == 0.0  # 0 correct characters remaining = 0.0 WPM