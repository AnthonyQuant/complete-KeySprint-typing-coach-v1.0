"""Edge case and boundary robustness test suite for KeySprint engine, passages, and database."""

import os
import sys
import pytest

# Dynamically add 'src' to Python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from engine import TypingEngine, EngineState
from passages import PassageManager
from analytics import AnalyticsDatabase
from achievements import AchievementManager


# --- Engine Boundary & Edge Cases ---

def test_backspace_at_start():
    """Verify backspacing on an empty input string does not crash or cause index errors."""
    engine = TypingEngine("test", duration_seconds=60)
    engine.process_backspace()
    assert len(engine.typed_text) == 0
    assert engine.calculate_wpm() == 0.0
    assert engine.calculate_accuracy() == 100.0


def test_zero_duration_handling():
    """Verify 0-second duration handles WPM calculation safely without division by zero."""
    engine = TypingEngine("hello", duration_seconds=0)
    engine.start_test()
    # Force elapsed time to 0
    engine.start_time = engine.end_time = 100.0
    assert engine.calculate_wpm() == 0.0


def test_typing_beyond_text_length():
    """Verify extra keypresses beyond target passage length are ignored."""
    engine = TypingEngine("hi", duration_seconds=60)
    engine.process_key("h")
    engine.process_key("i")
    engine.process_key("!")
    engine.process_key("?")
    assert engine.typed_text == "hi"
    assert engine.state == EngineState.FINISHED


def test_special_characters_and_newlines():
    """Verify Developer Mode code symbols (newlines, indentation, quotes, brackets) process correctly."""
    code_snippet = "def foo():\n    return [x * 2 for x in (1, 2)]"
    engine = TypingEngine(code_snippet, duration_seconds=60)

    for char in code_snippet:
        engine.process_key(char)

    assert engine.typed_text == code_snippet
    assert engine.calculate_accuracy() == 100.0
    assert engine.state == EngineState.FINISHED


# --- Passage Manager Edge Cases ---

def test_invalid_category_fallback():
    """Verify passing an unrecognized category falls back safely to 'general'."""
    pm = PassageManager("non_existent.json")
    passage = pm.get_passage(category="non_existent_category", allow_fallback=True)
    assert isinstance(passage, str)
    assert len(passage) > 0


def test_targeted_drill_with_empty_weak_keys():
    """Verify targeted drill generator handles empty weak keys list gracefully."""
    pm = PassageManager()
    drill = pm.generate_targeted_exercise([], word_count=10)
    assert isinstance(drill, str)
    assert len(drill) > 0


# --- Database & Analytics Edge Cases ---

def test_empty_database_aggregates(tmp_path):
    """Verify querying stats on a fresh database returns safe default zeros without crashing."""
    db_file = tmp_path / "empty.db"
    db = AnalyticsDatabase(str(db_file))

    stats = db.get_historical_stats()
    assert stats["total_tests"] == 0
    assert stats["avg_wpm"] == 0.0
    assert stats["best_wpm"] == 0.0
    assert stats["avg_accuracy"] == 0.0

    weak_keys = db.get_top_weak_keys(limit=5)
    assert weak_keys == []

    history = db.get_performance_history(limit=10)
    assert history == []