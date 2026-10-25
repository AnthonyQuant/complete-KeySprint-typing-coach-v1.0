"""Core typing mechanics, state management, and real-time metric calculations."""

"""Core typing mechanics, state management, and real-time metric calculations."""

import time
from enum import Enum
from typing import Dict, List, Tuple


class EngineState(Enum):
    IDLE = "IDLE"  # Waiting for first keystroke
    RUNNING = "RUNNING"  # Active typing test
    FINISHED = "FINISHED"  # Time expired or passage completed


class TypingEngine:
    def __init__(self, target_text: str, duration_seconds: int = 60):
        self.target_text: str = target_text
        self.duration_seconds: int = duration_seconds

        self.typed_text: str = ""
        self.state: EngineState = EngineState.IDLE

        self.start_time: float = 0.0
        self.end_time: float = 0.0

        # Keystroke analytics
        self.total_keystrokes: int = 0
        self.uncorrected_errors: int = 0
        self.character_errors: Dict[str, Dict[str, int]] = {}  # expected -> {typed: count}

    def start_test(self) -> None:
        """Starts the timer on first keystroke."""
        if self.state == EngineState.IDLE:
            self.state = EngineState.RUNNING
            self.start_time = time.time()

    def process_key(self, char_typed: str) -> None:
        """Processes a single character input."""
        if self.state == EngineState.FINISHED:
            return

        if self.state == EngineState.IDLE:
            self.start_test()

        # Prevent typing beyond text length
        if len(self.typed_text) >= len(self.target_text):
            return

        expected_char = self.target_text[len(self.typed_text)]
        self.typed_text += char_typed
        self.total_keystrokes += 1

        # Record miskey frequency for Weakness Analyzer
        if char_typed != expected_char:
            if expected_char not in self.character_errors:
                self.character_errors[expected_char] = {}
            self.character_errors[expected_char][char_typed] = (
                    self.character_errors[expected_char].get(char_typed, 0) + 1
            )

        # Complete test if full text typed
        if len(self.typed_text) == len(self.target_text):
            self.finish_test()

    def process_backspace(self) -> None:
        """Removes the last typed character."""
        if self.state == EngineState.RUNNING and len(self.typed_text) > 0:
            self.typed_text = self.typed_text[:-1]

    def finish_test(self) -> None:
        """Ends the active test."""
        if self.state == EngineState.RUNNING:
            self.state = EngineState.FINISHED
            self.end_time = time.time()

    def get_elapsed_seconds(self) -> float:
        """Returns active time elapsed."""
        if self.state == EngineState.IDLE:
            return 0.0
        elif self.state == EngineState.RUNNING:
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration_seconds:
                self.finish_test()
                return float(self.duration_seconds)
            return elapsed
        else:
            return min(self.end_time - self.start_time, float(self.duration_seconds))

    def calculate_wpm(self) -> float:
        """
        Calculates Gross Words Per Minute.
        Standard Formula: (Characters Typed / 5) / Elapsed Minutes
        """
        elapsed_min = self.get_elapsed_seconds() / 60.0
        if elapsed_min <= 0:
            return 0.0

        # Standard WPM definition: 1 word = 5 characters
        gross_wpm = (len(self.typed_text) / 5.0) / elapsed_min
        return round(gross_wpm, 2)

    def calculate_accuracy(self) -> float:
        """
        Calculates Accuracy percentage matching target text.
        Formula: (Correct Characters / Total Typed Characters) * 100
        """
        if not self.typed_text:
            return 100.0

        correct_chars = sum(
            1 for i, char in enumerate(self.typed_text)
            if i < len(self.target_text) and char == self.target_text[i]
        )
        accuracy = (correct_chars / len(self.typed_text)) * 100.0
        return round(accuracy, 2)

    def get_character_status(self) -> List[Tuple[str, str]]:
        """
        Returns list of (char, status) for UI rendering:
        Status options: 'correct', 'incorrect', 'untyped', 'cursor'
        """
        status_list = []
        typed_len = len(self.typed_text)

        for idx, char in enumerate(self.target_text):
            if idx < typed_len:
                if self.typed_text[idx] == char:
                    status_list.append((char, "correct"))
                else:
                    status_list.append((char, "incorrect"))
            elif idx == typed_len and self.state != EngineState.FINISHED:
                status_list.append((char, "cursor"))
            else:
                status_list.append((char, "untyped"))

        return status_list
