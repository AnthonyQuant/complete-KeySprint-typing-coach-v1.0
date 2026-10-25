"""Dynamic passage generator, vocabulary banks, and Developer Mode snippet engine."""

import json
import os
import random
from typing import Dict, List, Optional


# Vocabulary pools for dynamic Monkeytype-style text generation
COMMON_WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it", "for",
    "not", "on", "with", "as", "you", "do", "at", "this", "but", "his",
    "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my",
    "one", "all", "would", "there", "their", "what", "so", "up", "out", "if",
    "about", "who", "get", "which", "go", "me", "when", "make", "can", "like",
    "time", "no", "just", "him", "know", "take", "people", "into", "year", "your",
    "good", "some", "could", "them", "see", "other", "than", "then", "now", "look",
    "only", "come", "its", "over", "think", "also", "back", "after", "use", "two",
    "how", "our", "work", "first", "well", "way", "even", "new", "want", "because",
    "any", "these", "give", "day", "most", "us", "code", "data", "system", "logic"
]

PUNCTUATION_SYMBOLS = [
    "hello,", "world!", "test;", "'quote'", "\"string\"", "(parentheses)",
    "[index]", "{key: value}", "x == y", "a != b", "val += 1", "rate = 95.5%",
    "item_1,", "item_2;", "result = (a + b) * c;", "# comment line", "flag = True;"
]

PYTHON_TEMPLATES = [
    "def process_data(items: list) -> dict:\n    return {i: items[i] for i in range(len(items)) if items[i] > 0}",
    "class EngineManager:\n    def __init__(self, name: str):\n        self.name = name\n        self.active = True",
    "for key, value in config.items():\n    if value.get('enabled', False):\n        logger.info(f'Running {key}')",
    "try:\n    result = calculate_wpm(typed_chars, elapsed_time)\nexcept ZeroDivisionError:\n    result = 0.0",
    "import math\nfrom typing import List, Tuple\n\ndef calculate_accuracy(correct: int, total: int) -> float:\n    return round((correct / total) * 100.0, 2) if total > 0 else 100.0",
    "def binary_search(arr: list, target: int) -> int:\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1"
]

# Preserved for backward compatibility with unit tests
DEFAULT_PASSAGES: Dict[str, List[str]] = {
    "general": COMMON_WORDS,
    "punctuation": PUNCTUATION_SYMBOLS,
    "developer": PYTHON_TEMPLATES
}


class PassageManager:
    def __init__(self, json_path: str = "data/passages.json"):
        self.json_path = json_path
        self.passages: Dict[str, List[str]] = self.load_passages()

    def load_passages(self) -> Dict[str, List[str]]:
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except (json.JSONDecodeError, IOError):
                pass
        return DEFAULT_PASSAGES

    def get_passage(self, category: str = "general", word_count: int = 25, allow_fallback: bool = True) -> str:
        """
        Generates a fresh dynamic passage on every call based on the selected category.
        """
        category_key = category.lower()

        if category_key == "general":
            return " ".join(random.choices(COMMON_WORDS, k=word_count))

        elif category_key == "punctuation":
            mixed = [
                random.choice(COMMON_WORDS) if random.random() > 0.45 else random.choice(PUNCTUATION_SYMBOLS)
                for _ in range(word_count)
            ]
            return " ".join(mixed)

        elif category_key == "developer":
            return random.choice(PYTHON_TEMPLATES)

        elif allow_fallback:
            return " ".join(random.choices(COMMON_WORDS, k=word_count))
        else:
            raise ValueError(f"Category '{category}' not found.")

    def generate_targeted_exercise(self, weak_keys: List[str], word_count: int = 20) -> str:
        """
        Generates a custom practice drill focusing on words containing past weak keys.
        """
        if not weak_keys:
            return self.get_passage("general", word_count=word_count)

        candidate_words = [w for w in COMMON_WORDS if any(k in w for k in weak_keys)]

        if not candidate_words:
            return " ".join([f"key_{k}_{random.choice(weak_keys)}" for k in random.choices(weak_keys, k=word_count)])

        selected = [random.choice(candidate_words) for _ in range(word_count)]
        return " ".join(selected)