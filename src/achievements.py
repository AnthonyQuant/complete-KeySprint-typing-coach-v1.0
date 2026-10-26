"""Achievement tracking system for KeySprint."""

import os
import sqlite3
from typing import Dict, List, Set, Any
from engine import TypingEngine

# Resolve root directory relative to this file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_ACHIEVEMENTS_DB = os.path.join(BASE_DIR, "data", "achievements.db")

# Catalog of available achievements for UI rendering
ACHIEVEMENTS: Dict[str, Dict[str, Any]] = {
    "first_sprint": {
        "id": "first_sprint",
        "title": "First Sprint",
        "desc": "Complete 1st test session",
        "icon": "🏃"
    },
    "speed_demon": {
        "id": "speed_demon",
        "title": "Speed Demon",
        "desc": "Reach 80+ WPM",
        "icon": "⚡"
    },
    "flawless_code": {
        "id": "flawless_code",
        "title": "Flawless Code",
        "desc": "Complete a FULL Developer Mode passage with 100% accuracy.",
        "icon": "💻"
    },
    "ironclad": {
        "id": "ironclad",
        "title": "Ironclad",
        "desc": "Achieve 100% accuracy on a test with at least 15 words.",
        "icon": "🛡️"
    }
}


class AchievementManager:
    def __init__(self, db_path: str = DEFAULT_ACHIEVEMENTS_DB):
        self.db_path = db_path
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Initializes SQLite table for tracking unlocked achievements."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unlocked_achievements (
                    achievement_id TEXT PRIMARY KEY,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @property
    def achievements(self) -> Set[str]:
        """Returns set of all unlocked achievement IDs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT achievement_id FROM unlocked_achievements")
            return {row[0] for row in cursor.fetchall()}

    def get_unlocked_ids(self) -> List[Dict[str, Any]]:
        """Returns list of unlocked achievement dictionaries containing 'id' keys."""
        unlocked_set = self.achievements
        return [ACHIEVEMENTS[aid] for aid in unlocked_set if aid in ACHIEVEMENTS]

    def get_all_achievements(self) -> List[Dict[str, Any]]:
        """Returns list of all achievements with their current unlock status."""
        unlocked = self.achievements
        res = []
        for ach_id, data in ACHIEVEMENTS.items():
            item = data.copy()
            item["unlocked"] = ach_id in unlocked
            res.append(item)
        return res

    def is_unlocked(self, achievement_id: str) -> bool:
        return achievement_id in self.achievements

    def unlock_badge(self, achievement_id: str) -> bool:
        """Attempts to unlock a badge. Returns True if newly unlocked, False if already unlocked."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO unlocked_achievements (achievement_id) VALUES (?)",
                (achievement_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def evaluate_session(
        self,
        engine: TypingEngine,
        category: str = "general",
        total_tests_count: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Evaluates a completed typing session against catalog thresholds and returns
        a list of newly unlocked achievement dictionaries.
        """
        newly_unlocked_ids = []

        # 1. First Sprint (Complete 1st test session)
        if engine.is_fully_completed or engine.total_keystrokes > 0 or total_tests_count >= 1:
            if self.unlock_badge("first_sprint"):
                newly_unlocked_ids.append("first_sprint")

        # 2. Speed Demon (Reach 80+ Net WPM)
        if engine.calculate_net_wpm() >= 80.0:
            if self.unlock_badge("speed_demon"):
                newly_unlocked_ids.append("speed_demon")

        # 3. Flawless Code (100% accuracy on a FULL Developer Mode passage)
        if category == "developer" and engine.is_fully_completed and engine.calculate_final_accuracy() == 100.0:
            if self.unlock_badge("flawless_code"):
                newly_unlocked_ids.append("flawless_code")

        # 4. Ironclad (100% accuracy on any test with at least 15 words)
        words_typed = len(engine.typed_text.strip().split())
        if engine.calculate_final_accuracy() == 100.0 and words_typed >= 15 and engine.is_fully_completed:
            if self.unlock_badge("ironclad"):
                newly_unlocked_ids.append("ironclad")

        return [ACHIEVEMENTS[aid] for aid in newly_unlocked_ids if aid in ACHIEVEMENTS]