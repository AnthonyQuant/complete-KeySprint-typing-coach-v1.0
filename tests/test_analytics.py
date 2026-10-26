"""Unit tests for AnalyticsDatabase logging, weakness analysis, schema migrations, and dual metrics."""

import os
import sys
import sqlite3
import pytest

# Dynamically add 'src' directory to Python module search path
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
    assert stats["total_time_seconds"] == 0
    assert stats["best_wpm"] == 0.0
    assert stats["avg_accuracy"] == 0.0


def test_log_session_and_mean_keys(test_db):
    engine = TypingEngine("python", duration_seconds=60)
    for c in "python":
        engine.process_key(c)
    engine.finish_test()

    session_id = test_db.log_session(engine, category="developer")
    assert session_id > 0

    stats = test_db.get_historical_stats()
    assert stats["total_tests"] == 1
    assert stats["avg_accuracy"] == 100.0


def test_error_rate_calculation_and_threshold(tmp_path):
    """Verify get_top_weak_keys calculates error percentages and respects min_occurrences threshold."""
    db_file = tmp_path / "test_analytics.db"
    db = AnalyticsDatabase(str(db_file))

    # Engine simulating 10 encounters with 'e' (1 error -> 10.0% error rate)
    # and 2 encounters with 'z' (1 error -> 50.0% error rate, but below min_occurrences=5 threshold)
    engine = TypingEngine("eeeeeeeeeezz", duration_seconds=60)
    for char in "eeeeeeeeeezz":
        engine.process_key(char)

    # Set 1 miskey error for 'e' and 1 for 'z'
    engine.character_errors = {
        "e": {"x": 1},
        "z": {"x": 1}
    }
    engine.finish_test()

    db.log_session(engine, category="general")

    # With min_occurrences=5, 'z' (2 occurrences) is filtered out; 'e' (10 occurrences, 1 error) is ranked
    weak = db.get_top_weak_keys(limit=5, min_occurrences=5)
    assert len(weak) == 1
    assert weak[0][0] == "e"
    assert weak[0][1] == 10.0


def test_fallback_when_below_threshold(tmp_path):
    """Verify fallback mechanism when no character meets the min_occurrences threshold."""
    db_file = tmp_path / "test_analytics.db"
    db = AnalyticsDatabase(str(db_file))

    engine = TypingEngine("z", duration_seconds=60)
    engine.process_key("a")  # 1 occurrence, 1 error
    engine.character_errors = {"z": {"a": 1}}
    engine.finish_test()

    db.log_session(engine, category="general")

    # Fallback triggers and ranks 'z' by raw error count
    weak = db.get_top_weak_keys(limit=5, min_occurrences=5)
    assert len(weak) == 1
    assert weak[0][0] == "z"


def test_dual_metrics_logging_and_migration(tmp_path):
    """Verify log_session persists gross WPM and keystroke accuracy alongside standard metrics."""
    db_file = tmp_path / "test_analytics.db"
    db = AnalyticsDatabase(str(db_file))

    engine = TypingEngine("py", duration_seconds=60)
    engine.process_key("p")
    engine.process_key("x")  # Typo
    engine.process_backspace()
    engine.process_key("y")  # Correction

    session_id = db.log_session(engine, category="general")
    assert session_id > 0

    # Retrieve logged session record directly from SQLite
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT wpm, gross_wpm, accuracy, keystroke_accuracy FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()

        assert row is not None
        net_wpm, gross_wpm, final_acc, keystroke_acc = row

        assert final_acc == 100.0
        assert keystroke_acc == 66.67  # 2 correct out of 3 keystrokes
        assert gross_wpm >= net_wpm


def test_database_schema_migration_for_legacy_tables(tmp_path):
    """Verify _init_db automatically migrates legacy DB schemas missing gross_wpm/keystroke_accuracy."""
    db_file = tmp_path / "legacy.db"

    # Pre-create legacy sessions table lacking new columns
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("""
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                category TEXT,
                wpm REAL,
                accuracy REAL,
                duration_seconds INTEGER,
                total_keystrokes INTEGER
            )
        """)
        conn.commit()

    # Initializing AnalyticsDatabase triggers ALTER TABLE migration
    db = AnalyticsDatabase(str(db_file))

    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sessions)")
        cols = [col[1] for col in cursor.fetchall()]

        assert "gross_wpm" in cols
        assert "keystroke_accuracy" in cols