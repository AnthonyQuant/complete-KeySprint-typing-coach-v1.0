"""Core typing engine logic, timer precision, state management, and dual metrics for KeySprint."""

import time
from enum import Enum
from typing import Dict, List, Tuple


class EngineState(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"


class TypingEngine:
    def __init__(self, target_text: str = "", duration_seconds: int = 60):
        self.target_text: str = target_text
        self.duration_seconds: int = duration_seconds

        self.typed_text: str = ""
        self.state: EngineState = EngineState.IDLE

        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.total_keystrokes: int = 0

        # Nested dictionary mapping: expected_char -> {typed_char: error_count}
        self.character_errors: Dict[str, Dict[str, int]] = {}

        # Dictionary mapping: expected_char -> total_occurrences_count
        self.character_occurrences: Dict[str, int] = {}

    def start_test(self) -> None:
        """Starts the typing test timer using high-precision monotonic clock."""
        if self.state == EngineState.IDLE:
            self.state = EngineState.RUNNING
            self.start_time = time.monotonic()

    def finish_test(self) -> None:
        """Stops the typing test timer."""
        if self.state == EngineState.RUNNING:
            self.state = EngineState.FINISHED
            self.end_time = time.monotonic()

    def process_key(self, char: str) -> None:
        """Processes character input keypresses."""
        if self.state == EngineState.FINISHED:
            return

        if self.state == EngineState.IDLE:
            self.start_test()

        if len(self.typed_text) < len(self.target_text):
            expected = self.target_text[len(self.typed_text)]

            # Record total occurrences encountered for this expected character
            self.character_occurrences[expected] = self.character_occurrences.get(expected, 0) + 1

            # Record miskeys
            if char != expected:
                if expected not in self.character_errors:
                    self.character_errors[expected] = {}
                self.character_errors[expected][char] = self.character_errors[expected].get(char, 0) + 1

            self.typed_text += char
            self.total_keystrokes += 1

            # Automatically complete test when full text matches target
            if self.typed_text == self.target_text:
                self.finish_test()

    def process_backspace(self) -> None:
        """Removes the last typed character without incrementing total keystrokes."""
        if self.state == EngineState.FINISHED or len(self.typed_text) == 0:
            return
        self.typed_text = self.typed_text[:-1]

    def get_elapsed_seconds(self) -> float:
        """Observational getter for elapsed test time in seconds, capped at duration if finished."""
        if self.state == EngineState.IDLE:
            return 0.0
        if self.state == EngineState.RUNNING:
            return time.monotonic() - self.start_time

        raw_elapsed = self.end_time - self.start_time
        if not self.is_fully_completed and raw_elapsed > self.duration_seconds:
            return float(self.duration_seconds)
        return raw_elapsed

    @property
    def is_fully_completed(self) -> bool:
        """Returns True if the target text is fully matched."""
        return self.typed_text == self.target_text and len(self.target_text) > 0

    def get_character_status(self) -> List[Tuple[str, str]]:
        """Returns list of (char, status_tag) tuples for UI highlighting."""
        res = []
        for i, char in enumerate(self.target_text):
            if i < len(self.typed_text):
                if self.typed_text[i] == char:
                    res.append((char, "correct"))
                else:
                    res.append((char, "incorrect"))
            elif i == len(self.typed_text):
                res.append((char, "cursor"))
            else:
                res.append((char, "untyped"))
        return res

    # --- Accuracy Metrics ---

    def calculate_final_accuracy(self) -> float:
        """Percentage of characters in the current typed buffer matching target_text."""
        if len(self.typed_text) == 0:
            return 100.0
        correct_chars = sum(
            1 for i, c in enumerate(self.typed_text)
            if i < len(self.target_text) and c == self.target_text[i]
        )
        acc = (correct_chars / len(self.typed_text)) * 100.0
        return round(min(100.0, max(0.0, acc)), 2)

    def calculate_keystroke_accuracy(self) -> float:
        """
        Percentage of total character-entry attempts that were correct,
        accounting for corrected mistakes and backspaced keystrokes.
        """
        if self.total_keystrokes == 0:
            return 100.0
        total_errors = sum(sum(typed_map.values()) for typed_map in self.character_errors.values())
        correct_attempts = max(0, self.total_keystrokes - total_errors)
        acc = (correct_attempts / self.total_keystrokes) * 100.0
        return round(min(100.0, max(0.0, acc)), 2)

    def calculate_accuracy(self) -> float:
        """Backward-compatible alias for final-text accuracy."""
        return self.calculate_final_accuracy()

    # --- Speed Metrics ---

    def calculate_net_wpm(self) -> float:
        """Net WPM based strictly on correctly typed characters remaining in the final text buffer."""
        elapsed_min = self.get_elapsed_seconds() / 60.0
        if elapsed_min <= 0:
            return 0.0
        correct_chars = sum(
            1 for i, c in enumerate(self.typed_text)
            if i < len(self.target_text) and c == self.target_text[i]
        )
        net_words = correct_chars / 5.0
        return round(net_words / elapsed_min, 1)

    def calculate_gross_wpm(self) -> float:
        """Gross (Raw) WPM based on total character-entry keystrokes over time."""
        elapsed_min = self.get_elapsed_seconds() / 60.0
        if elapsed_min <= 0:
            return 0.0
        raw_words = self.total_keystrokes / 5.0
        return round(raw_words / elapsed_min, 1)

    def calculate_wpm(self) -> float:
        """Backward-compatible alias for Net WPM."""
        return self.calculate_net_wpm()