"""Unit tests for weakness frequency counts and data persistence."""

"""Unit tests for AnalyticsDatabase SQLite operations and Weakness Analyzer."""

import os
import sys
import pytest

# Dynamically add 'src' to Python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from engine import TypingEngine
from analytics import AnalyticsDatabase


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_history.db"
    return AnalyticsDatabase(str(db_file))


def test_database_initialization(test_db):
    stats = test_db.get_historical_stats()
    assert stats["total_tests"] == 0
    assert stats["avg_wpm"] == 0.0
    assert stats["best_wpm"] == 0.0


def test_log_session_and_weak_keys(test_db):
    engine = TypingEngine("python", duration_seconds=60)
    # Type 'pythxx' (errors on expected 'o' and 'n')
    for c in "pythxx":
        engine.process_key(c)
    engine.finish_test()

    session_id = test_db.log_session(engine, category="developer")
    assert session_id > 0

    stats = test_db.get_historical_stats()
    assert stats["total_tests"] == 1
    assert stats["avg_accuracy"] == 66.7

    weak_keys = test_db.get_top_weak_keys(limit=5)
    assert len(weak_keys) == 2
    expected_chars = [k[0] for k in weak_keys]
    assert "o" in expected_chars
    assert "n" in expected_chars
