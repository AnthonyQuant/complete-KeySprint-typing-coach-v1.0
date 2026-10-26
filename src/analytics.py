"""SQLite data persistence, historical performance analysis, and weakness analyzer for KeySprint."""

import os
import sqlite3
from typing import Any, Dict, List, Tuple
from engine import TypingEngine

# Resolve root directory relative to this file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "history.db")


class AnalyticsDatabase:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Initializes database tables and performs dynamic schema migrations if necessary."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Main sessions table with dual metric support
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category TEXT,
                    wpm REAL,
                    gross_wpm REAL DEFAULT 0.0,
                    accuracy REAL,
                    keystroke_accuracy REAL DEFAULT 100.0,
                    duration_seconds INTEGER,
                    total_keystrokes INTEGER
                )
            """)

            # Migration check for existing databases upgrading to dual metrics
            cursor.execute("PRAGMA table_info(sessions)")
            session_cols = [col[1] for col in cursor.fetchall()]
            if "gross_wpm" not in session_cols:
                cursor.execute("ALTER TABLE sessions ADD COLUMN gross_wpm REAL DEFAULT 0.0")
            if "keystroke_accuracy" not in session_cols:
                cursor.execute("ALTER TABLE sessions ADD COLUMN keystroke_accuracy REAL DEFAULT 100.0")

            # 2. Character error & occurrence tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS character_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    expected_char TEXT,
                    typed_char TEXT,
                    error_count INTEGER,
                    occurrences_count INTEGER DEFAULT 0,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
            """)

            cursor.execute("PRAGMA table_info(character_errors)")
            error_cols = [col[1] for col in cursor.fetchall()]
            if "occurrences_count" not in error_cols:
                cursor.execute("ALTER TABLE character_errors ADD COLUMN occurrences_count INTEGER DEFAULT 0")

            conn.commit()

    def log_session(self, engine: TypingEngine, category: str) -> int:
        """Logs a completed typing session including dual speed and accuracy metrics into SQLite."""
        net_wpm = engine.calculate_net_wpm()
        gross_wpm = engine.calculate_gross_wpm()
        final_acc = engine.calculate_final_accuracy()
        keystroke_acc = engine.calculate_keystroke_accuracy()
        elapsed = int(engine.get_elapsed_seconds())

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (category, wpm, gross_wpm, accuracy, keystroke_accuracy, duration_seconds, total_keystrokes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (category, net_wpm, gross_wpm, final_acc, keystroke_acc, elapsed, engine.total_keystrokes))

            session_id = cursor.lastrowid

            # Log character occurrences and miskey errors
            for expected_char, total_occ in engine.character_occurrences.items():
                errors_dict = engine.character_errors.get(expected_char, {})
                if not errors_dict:
                    cursor.execute("""
                        INSERT INTO character_errors (session_id, expected_char, typed_char, error_count, occurrences_count)
                        VALUES (?, ?, ?, ?, ?)
                    """, (session_id, expected_char, "", 0, total_occ))
                else:
                    first = True
                    for typed_char, err_cnt in errors_dict.items():
                        occ_to_log = total_occ if first else 0
                        first = False
                        cursor.execute("""
                            INSERT INTO character_errors (session_id, expected_char, typed_char, error_count, occurrences_count)
                            VALUES (?, ?, ?, ?, ?)
                        """, (session_id, expected_char, typed_char, err_cnt, occ_to_log))

            conn.commit()
            return session_id

    def get_historical_stats(self) -> Dict[str, Any]:
        """Returns aggregate historical statistics across all recorded sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*),
                    COALESCE(SUM(duration_seconds), 0),
                    COALESCE(MAX(wpm), 0.0),
                    COALESCE(AVG(accuracy), 0.0),
                    COALESCE(AVG(wpm), 0.0)
                FROM sessions
            """)
            row = cursor.fetchone()
            if not row or row[0] == 0:
                return {
                    "total_tests": 0,
                    "total_time_seconds": 0,
                    "total_time": 0,
                    "avg_wpm": 0.0,
                    "best_wpm": 0.0,
                    "avg_accuracy": 0.0
                }
            return {
                "total_tests": row[0],
                "total_time_seconds": row[1],
                "total_time": row[1],
                "avg_wpm": round(row[4], 1),
                "best_wpm": round(row[2], 1),
                "avg_accuracy": round(row[3], 2)
            }

    def get_top_weak_keys(self, limit: int = 5, min_occurrences: int = 5) -> List[Tuple[str, float]]:
        """
        Calculates error percentage rates per character across all logged sessions.
        Returns list of tuples: (character, error_percentage).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    expected_char,
                    SUM(error_count) as total_errors,
                    SUM(occurrences_count) as total_occurrences
                FROM character_errors
                WHERE expected_char IS NOT NULL AND expected_char != ''
                GROUP BY expected_char
                HAVING total_occurrences >= ?
            """, (min_occurrences,))
            rows = cursor.fetchall()

            results = []
            for char, errs, occs in rows:
                if occs > 0:
                    rate = (errs / occs) * 100.0
                    results.append((char, round(rate, 1)))

            # Fallback ranking by raw error count if no key reaches min_occurrences threshold
            if not results:
                cursor.execute("""
                    SELECT expected_char, SUM(error_count) as total_errors
                    FROM character_errors
                    WHERE expected_char IS NOT NULL AND expected_char != ''
                    GROUP BY expected_char
                    HAVING total_errors > 0
                    ORDER BY total_errors DESC
                    LIMIT ?
                """, (limit,))
                fallback_rows = cursor.fetchall()
                results = [(char, float(errs)) for char, errs in fallback_rows]

            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]

    def get_recent_wpm_history(self, limit: int = 10) -> List[Tuple[int, float]]:
        """Returns list of (session_id, wpm) for simple progression charting."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, wpm FROM sessions
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return list(reversed(rows))

    def get_performance_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetches list of recent typing sessions for performance history tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, category, wpm, gross_wpm, accuracy, keystroke_accuracy, duration_seconds
                FROM sessions
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            history = []
            for r in rows:
                history.append({
                    "id": r[0],
                    "timestamp": r[1],
                    "category": r[2],
                    "wpm": r[3],
                    "gross_wpm": r[4],
                    "accuracy": r[5],
                    "keystroke_accuracy": r[6],
                    "duration_seconds": r[7]
                })
            return history