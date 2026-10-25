"""SQLite data persistence, historical performance analysis, and Weakness Analyzer."""

"""SQLite data persistence, historical performance analysis, and Weakness Analyzer."""

import sqlite3
import time
from typing import Dict, List, Tuple
from engine import TypingEngine


class AnalyticsDatabase:
    def __init__(self, db_path: str = "data/history.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Creates database schema if tables do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Test Sessions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    wpm REAL NOT NULL,
                    accuracy REAL NOT NULL,
                    total_keystrokes INTEGER NOT NULL
                )
            """)
            # Character Miskey Frequencies Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS character_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    expected_char TEXT NOT NULL,
                    typed_char TEXT NOT NULL,
                    error_count INTEGER NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def log_session(self, engine: TypingEngine, category: str) -> int:
        """Saves a completed test session and records character error frequencies."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (timestamp, duration_seconds, category, wpm, accuracy, total_keystrokes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                time.time(),
                engine.duration_seconds,
                category,
                engine.calculate_wpm(),
                engine.calculate_accuracy(),
                engine.total_keystrokes
            ))
            session_id = cursor.lastrowid

            # Save character error occurrences
            for expected_char, typed_dict in engine.character_errors.items():
                for typed_char, count in typed_dict.items():
                    cursor.execute("""
                        INSERT INTO character_errors (session_id, expected_char, typed_char, error_count)
                        VALUES (?, ?, ?, ?)
                    """, (session_id, expected_char, typed_char, count))

            conn.commit()
            return session_id

    def get_historical_stats(self) -> Dict[str, float]:
        """Returns aggregate statistics across all logged test sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*), 
                    COALESCE(AVG(wpm), 0.0), 
                    COALESCE(MAX(wpm), 0.0), 
                    COALESCE(AVG(accuracy), 0.0)
                FROM sessions
            """)
            row = cursor.fetchone()
            return {
                "total_tests": row[0],
                "avg_wpm": round(row[1], 1),
                "best_wpm": round(row[2], 1),
                "avg_accuracy": round(row[3], 1)
            }

    def get_top_weak_keys(self, limit: int = 5) -> List[Tuple[str, int]]:
        """
        Identifies characters with highest error counts across all past sessions.
        Returns list of (expected_char, total_error_count).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT expected_char, SUM(error_count) as total_err
                FROM character_errors
                GROUP BY expected_char
                ORDER BY total_err DESC
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()

    def get_recent_wpm_history(self, limit: int = 10) -> List[Tuple[int, float]]:
        """Returns list of (session_id, wpm) for progression charting."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, wpm FROM sessions
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return list(reversed(rows))

    def get_performance_history(self, limit: int = 15) -> List[Tuple[int, float, float]]:
        """
        Returns list of (session_id, wpm, accuracy) ordered chronologically
        for performance trend visualization.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, wpm, accuracy FROM sessions
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return list(reversed(rows))
