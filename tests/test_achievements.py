"""Unit tests for achievement badge criteria and persistence."""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from engine import TypingEngine
from achievements import AchievementManager


def test_initial_unlocked_empty(tmp_path):
    db_file = tmp_path / "test_achievements.db"
    mgr = AchievementManager(str(db_file))
    assert mgr.get_unlocked_ids() == []


def test_first_sprint_unlock(tmp_path):
    db_file = tmp_path / "test_achievements.db"
    mgr = AchievementManager(str(db_file))
    engine = TypingEngine("hello world", duration_seconds=60)
    engine.process_key("h")
    engine.finish_test()

    unlocked = mgr.evaluate_session(engine, category="general", total_tests_count=1)
    unlocked_ids = [a["id"] for a in unlocked]
    assert "first_sprint" in unlocked_ids


def test_partial_developer_mode_does_not_unlock_flawless_code(tmp_path):
    """Verify partial snippet completion with 100% accuracy DOES NOT unlock flawless_code."""
    db_file = tmp_path / "test_achievements.db"
    mgr = AchievementManager(str(db_file))

    code_snippet = "def foo():\n    return 42"
    engine = TypingEngine(code_snippet, duration_seconds=60)

    # Type only the first 3 characters correctly ("def")
    for char in "def":
        engine.process_key(char)

    engine.finish_test()
    assert engine.calculate_accuracy() == 100.0
    assert not engine.is_fully_completed

    unlocked = mgr.evaluate_session(engine, category="developer", total_tests_count=1)
    unlocked_ids = [a["id"] for a in unlocked]
    assert "flawless_code" not in unlocked_ids


def test_flawless_code_unlock_on_full_completion(tmp_path):
    """Verify completing the entire developer snippet with 100% accuracy unlocks flawless_code."""
    db_file = tmp_path / "test_achievements.db"
    mgr = AchievementManager(str(db_file))

    code_snippet = "def foo():\n    return 42"
    engine = TypingEngine(code_snippet, duration_seconds=60)

    for char in code_snippet:
        engine.process_key(char)

    engine.finish_test()
    assert engine.calculate_accuracy() == 100.0
    assert engine.is_fully_completed

    unlocked = mgr.evaluate_session(engine, category="developer", total_tests_count=1)
    unlocked_ids = [a["id"] for a in unlocked]
    assert "flawless_code" in unlocked_ids