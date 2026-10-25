"""Unit tests for AchievementManager logic and unlock criteria."""

import os
import sys
import pytest

# Dynamically add 'src' to Python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from engine import TypingEngine
from achievements import AchievementManager


@pytest.fixture
def ach_mgr(tmp_path):
    db_file = tmp_path / "test_achievements.db"
    return AchievementManager(str(db_file))


def test_initial_unlocked_empty(ach_mgr):
    assert len(ach_mgr.get_unlocked_ids()) == 0


def test_first_sprint_unlock(ach_mgr):
    engine = TypingEngine("hello world", duration_seconds=60)
    engine.process_key("h")
    engine.finish_test()

    newly_unlocked = ach_mgr.evaluate_session(engine, category="general", total_tests_count=1)
    unlocked_ids = [a["id"] for a in newly_unlocked]
    assert "first_sprint" in unlocked_ids


def test_flawless_code_unlock(ach_mgr):
    engine = TypingEngine("def foo():", duration_seconds=60)
    for c in "def foo():":
        engine.process_key(c)
    engine.finish_test()

    newly_unlocked = ach_mgr.evaluate_session(engine, category="developer", total_tests_count=1)
    unlocked_ids = [a["id"] for a in newly_unlocked]
    assert "flawless_code" in unlocked_ids