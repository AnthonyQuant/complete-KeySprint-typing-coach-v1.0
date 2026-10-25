"""Local challenge and achievement criteria tracking."""

"""Local challenge and achievement criteria tracking."""

import sqlite3
from typing import Dict, List, Tuple
from engine import TypingEngine

ACHIEVEMENT_DEFINITIONS = [
    {
        "id": "first_sprint",
        "title": "First Sprint",
        "desc": "Complete your first typing test session.",
        "icon": "🚀"
    },
    {
        "id": "speed_demon",
        "title": "Speed Demon",
        "desc": "Reach 40+ WPM with 95%+ accuracy.",
        "icon": "⚡"
    },
    {
        "id": "century_club",
        "title": "Century Club",
        "desc": "Reach 100+ WPM in any test category.",
        "icon": "🔥"
    },
    {
        "id": "flawless_code",
        "title": "Flawless Code",
        "desc": "Complete a Developer Mode test with 100% accuracy.",
        "icon": "💻"
    },
    {
        "id": "ironclad",
        "title": "Ironclad",
        "desc": "Complete a 120s test with 98%+ accuracy.",
        "icon": "🛡️"
    },
    {
        "id": "dedicated_typist",
        "title": "Dedicated Typist",
        "desc": "Complete 10 total test sessions.",
        "icon": "🏆"
    }
]


class AchievementManager:
    def __init__(self, db_path: str = "data/history.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Ensures achievements persistence table exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unlocked_achievements (
                    achievement_id TEXT PRIMARY KEY,
                    unlocked_at REAL NOT NULL
                )
            """)
            conn.commit()

    def get_unlocked_ids(self) -> List[str]:
        """Returns list of unlocked achievement IDs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT achievement_id FROM unlocked_achievements")
            return [row[0] for row in cursor.fetchall()]

    def evaluate_session(self, engine: TypingEngine, category: str, total_tests_count: int) -> List[Dict[str, str]]:
        """
        Evaluates session metrics against defined goals.
        Unlocks new achievements in SQLite database and returns newly unlocked items.
        """
        wpm = engine.calculate_wpm()
        accuracy = engine.calculate_accuracy()
        duration = engine.duration_seconds

        already_unlocked = set(self.get_unlocked_ids())
        newly_unlocked = []

        # Rule Evaluations
        candidates = []

        # 1. First Sprint
        if total_tests_count >= 1:
            candidates.append("first_sprint")

        # 2. Speed Demon
        if wpm >= 40.0 and accuracy >= 95.0:
            candidates.append("speed_demon")

        # 3. Century Club
        if wpm >= 100.0:
            candidates.append("century_club")

        # 4. Flawless Code
        if category.lower() == "developer" and accuracy == 100.0:
            candidates.append("flawless_code")

        # 5. Ironclad
        if duration >= 120 and accuracy >= 98.0:
            candidates.append("ironclad")

        # 6. Dedicated Typist
        if total_tests_count >= 10:
            candidates.append("dedicated_typist")

        # Save new unlocks
        with self._get_connection() as conn:
            cursor = conn.cursor()
            import time
            for ach_id in candidates:
                if ach_id not in already_unlocked:
                    cursor.execute(
                        "INSERT OR IGNORE INTO unlocked_achievements (achievement_id, unlocked_at) VALUES (?, ?)",
                        (ach_id, time.time())
                    )
                    ach_info = next(a for a in ACHIEVEMENT_DEFINITIONS if a["id"] == ach_id)
                    newly_unlocked.append(ach_info)
            conn.commit()

        return newly_unlocked

    def get_all_achievements(self) -> List[Dict[str, str]]:
        """Returns all achievement definitions paired with their unlock status."""
        unlocked = set(self.get_unlocked_ids())
        result = []
        for ach in ACHIEVEMENT_DEFINITIONS:
            item = dict(ach)
            item["unlocked"] = ach["id"] in unlocked
            result.append(item)
        return result
