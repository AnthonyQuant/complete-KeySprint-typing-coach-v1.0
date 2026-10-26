"""Edge case and boundary robustness test suite for KeySprint engine, passages, and database."""

import os
import sys
import pytest

# Dynamically add 'src' to Python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from engine import TypingEngine, EngineState
from passages import PassageManager, DEFAULT_JSON_PATH
from analytics import AnalyticsDatabase, DEFAULT_DB_PATH
from achievements import AchievementManager, DEFAULT_ACHIEVEMENTS_DB


# --- Engine Boundary & Edge Cases ---

def test_backspace_at_start():
    """Typing backspace on an empty input string does not crash or cause index errors."""
    engine = TypingEngine("test", duration_seconds=60)
    engine.process_backspace()
    assert len(engine.typed_text) == 0
    assert engine.calculate_wpm() == 0.0
    assert engine.calculate_accuracy() == 100.0


def test_zero_duration_handling():
    """Verify 0-second duration handles WPM calculation safely without division by zero."""
    engine = TypingEngine("hello", duration_seconds=0)
    engine.start_test()
    engine.end_time = engine.start_time
    engine.state = EngineState.FINISHED
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
    code_snippet = 'def foo():\n    return [x * 2 for x in (1, 2)]'
    engine = TypingEngine(code_snippet, duration_seconds=60)

    for char in code_snippet:
        engine.process_key(char)

    assert engine.typed_text == code_snippet
    assert engine.calculate_accuracy() == 100.0
    assert engine.state == EngineState.FINISHED


def test_engine_is_fully_completed_flag():
    """Verify is_fully_completed returns True only when typed_text matches target_text completely."""
    engine = TypingEngine("abc", duration_seconds=60)
    assert not engine.is_fully_completed

    engine.process_key("a")
    engine.process_key("b")
    assert not engine.is_fully_completed

    engine.process_key("c")
    assert engine.is_fully_completed
    assert engine.state == EngineState.FINISHED


def test_multiline_newlines_and_tab_indentation():
    """Verify multiline text with newlines and 4-space tabs processes accurately."""
    snippet = "def test():\n    pass"
    engine = TypingEngine(snippet, duration_seconds=60)

    # Type "def test():"
    for char in "def test():":
        engine.process_key(char)

    # Type newline '\n'
    engine.process_key("\n")

    # Type Tab (4 spaces)
    for _ in range(4):
        engine.process_key(" ")

    # Type "pass"
    for char in "pass":
        engine.process_key(char)

    assert engine.typed_text == snippet
    assert engine.calculate_accuracy() == 100.0
    assert engine.is_fully_completed


# --- Passage Manager Edge Cases ---

def test_invalid_category_fallback():
    """Verify passing an unrecognized category falls back safely to 'general'."""
    pm = PassageManager()
    passage = pm.get_passage("non_existent_category", allow_fallback=True)
    assert isinstance(passage, str)
    assert len(passage) > 0


def test_targeted_drill_with_empty_weak_keys():
    """Verify targeted drill generation handles empty weak keys list gracefully."""
    pm = PassageManager()
    drill = pm.generate_targeted_exercise([], word_count=10)
    assert isinstance(drill, str)
    assert len(drill) > 0


# --- Path Resolution Edge Cases ---

def test_absolute_path_resolution():
    """Verify default paths resolve as absolute paths inside project data/ directory."""
    assert os.path.isabs(DEFAULT_DB_PATH)
    assert os.path.isabs(DEFAULT_JSON_PATH)
    assert os.path.isabs(DEFAULT_ACHIEVEMENTS_DB)

    assert DEFAULT_DB_PATH.endswith(os.path.join("data", "history.db"))
    assert DEFAULT_JSON_PATH.endswith(os.path.join("data", "passages.json"))
    assert DEFAULT_ACHIEVEMENTS_DB.endswith(os.path.join("data", "achievements.db"))


# --- Database & Analytics Edge Cases ---

def test_empty_database_aggregates(tmp_path):
    """Verify querying stats on a fresh database returns safe default zeroes without crashing."""
    db_file = tmp_path / "empty.db"
    db = AnalyticsDatabase(str(db_file))

    stats = db.get_historical_stats()
    assert stats["total_tests"] == 0
    assert stats["total_time_seconds"] == 0
    assert stats["best_wpm"] == 0.0
    assert stats["avg_accuracy"] == 0.0

    weak_keys = db.get_top_weak_keys()
    assert weak_keys == []

    history = db.get_performance_history(limit=10)
    assert history == []