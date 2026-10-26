"""Dynamic passage generator, vocabulary banks, and Developer Mode snippet engine for KeySprint."""

import json
import os
import random
from typing import Dict, List, Optional

# Resolve root directory relative to this file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_JSON_PATH = os.path.join(BASE_DIR, "data", "passages.json")


# Vocabulary pools for dynamic Monkeytype-style text generation
COMMON_WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for",
    "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his",
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
    "hello,", "world!", "test.", "quote:", '1', "(string)", "(parentheses)",
    "{index}", "key:", "value;", "x == y", "a = 1", "b = 10", "rate = 95.5%",
    "item_1", "item_2", "result = a + b;", "# Comment line", "Flag = True;"
]

# Curated practice collections for non-lowercase-letter weaknesses
PUNCTUATION_DRILLS = {
    ".": ["stop. wait. listen.", "data.process()", "item.value.get()"],
    ",": ["ready, set, go.", "alpha, beta, gamma", "one, two, three, four,"],
    ";": ["statement1; statement2;", "for (i=0; i<10; i++)", "import sys; print(sys.path)"],
    ":": ["key: value", "def run():", "if condition:", "dict[str: int]"],
    "!": ["Warning!", "Error: Failed!", "assert result is not None!"],
    "?": ["is_valid?", "value if cond else default", "exists ? true : false"],
    "\"": ['name = "KeySprint"', 'print("Hello, World!")', 'data["status"]'],
    "'": ["item = 'test'", "'single_quoted_string'", "user['id']"]
}

DEVELOPER_SYMBOL_DRILLS = {
    "(": ["func(a, b)", "calculate(val * 2)", "if (x > 0 and y < 10):"],
    ")": ["func(a, b)", "calculate(val * 2)", "if (x > 0 and y < 10):"],
    "[": ["items[0]", "matrix[i][j]", "data[1:5]"],
    "]": ["items[0]", "matrix[i][j]", "data[1:5]"],
    "{": ["{'key': 'value'}", "set_data = {1, 2, 3}", "f'Result: {val}'"],
    "}": ["{'key': 'value'}", "set_data = {1, 2, 3}", "f'Result: {val}'"],
    "_": ["temp_var", "__init__", "process_data_stream", "is_valid_user"],
    "=": ["total = 100", "status = True", "count += 1", "key == target"],
    "+": ["count + 1", "a + b", "total += val"],
    "-": ["total - 5", "item -> value", "count -= 1"],
    "<": ["x < y", "for i in range(len(arr) - 1):", "list[int]"],
    ">": ["x > y", "val >= 100", "stream -> output"]
}

UPPERCASE_DRILLS = [
    "API Standard Protocol", "JSON Schema Definition", "HTTP Request Headers",
    "SQL Database Connection", "GUI Interface Component", "WPM Accuracy Metric"
]

PYTHON_TEMPLATES = [
    "def process_data(items: list) -> dict:\n    return {i: items[i] for i in range(len(items)) if items[i] > 0}",
    "class EngineManager:\n    def __init__(self, name: str):\n        self.name = name\n        self.active = True",
    "for key, value in config.items():\n    if value.get('enabled', False):\n        logger.info(f'Running {key}')",
    "try:\n    result = calculate_wpm(typed_chars, elapsed_time)\nexcept ZeroDivisionError:\n    result = 0.0",
    "def calculate_accuracy(correct: int, total: int) -> float:\n    if total == 0:\n        return 100.0\n    return round((correct / total) * 100.0, 2)",
    "def binary_search(arr: list, target: int) -> int:\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1"
]

DEFAULT_PASSAGES: Dict[str, List[str]] = {
    "general": COMMON_WORDS,
    "punctuation": PUNCTUATION_SYMBOLS,
    "developer": PYTHON_TEMPLATES
}


class PassageManager:
    def __init__(self, json_path: str = DEFAULT_JSON_PATH):
        self.json_path = json_path
        self.passages: Dict[str, List[str]] = self._load_passages()
        self.last_passage: Optional[str] = None

    def _load_passages(self) -> Dict[str, List[str]]:
        """Loads custom passages from JSON if available, falling back to DEFAULT_PASSAGES."""
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except (json.JSONDecodeError, OSError):
                pass
        return DEFAULT_PASSAGES

    def get_passage(self, category: str = "general", word_count: int = 25, allow_fallback: bool = True) -> str:
        """
        Generates or fetches a passage for the specified category, prioritizing data loaded
        from data/passages.json while ensuring back-to-back repetitions are avoided.
        """
        category_key = category.lower()
        category_pool = self.passages.get(category_key, [])

        if category_key == "general":
            word_pool = category_pool if category_pool else COMMON_WORDS
            result = " ".join(random.choices(word_pool, k=word_count))

        elif category_key == "punctuation":
            punc_pool = category_pool if category_pool else PUNCTUATION_SYMBOLS
            word_pool = self.passages.get("general", COMMON_WORDS)
            mixed = []
            for _ in range(word_count):
                if random.random() > 0.45:
                    mixed.append(random.choice(punc_pool))
                else:
                    mixed.append(random.choice(word_pool))
            result = " ".join(mixed)

        elif category_key == "developer":
            snippet_pool = category_pool if category_pool else PYTHON_TEMPLATES
            available = [s for s in snippet_pool if s != self.last_passage]
            result = random.choice(available if available else snippet_pool)

        elif category_pool:
            available = [p for p in category_pool if str(p) != self.last_passage]
            selected = random.choice(available if available else category_pool)
            result = selected if isinstance(selected, str) else str(selected)

        elif allow_fallback:
            result = " ".join(random.choices(COMMON_WORDS, k=word_count))

        else:
            raise ValueError(f"Category '{category}' not found in passages repository.")

        self.last_passage = result
        return result

    def generate_targeted_exercise(self, weak_keys: List[str], word_count: int = 20) -> str:
        """
        Generates a custom practice drill intelligently targeting weak characters across
        letters, punctuation, uppercase, developer symbols, and whitespace.
        """
        if not weak_keys:
            return self.get_passage("general", word_count=word_count)

        pool: List[str] = []

        for key in weak_keys:
            if key == " ":
                pool.extend(["a b c", "one two three", "space test run", "word gap word"])
            elif key == "\n":
                pool.extend(["line1;\nline2;", "def fn():\n    pass", "if True:\n    return"])
            elif key in DEVELOPER_SYMBOL_DRILLS:
                pool.extend(DEVELOPER_SYMBOL_DRILLS[key])
            elif key in PUNCTUATION_DRILLS:
                pool.extend(PUNCTUATION_DRILLS[key])
            elif key.isupper():
                matching_upper = [phrase for phrase in UPPERCASE_DRILLS if key in phrase]
                pool.extend(matching_upper if matching_upper else UPPERCASE_DRILLS)
            else:
                matching_words = [w for w in COMMON_WORDS if key in w]
                if matching_words:
                    pool.extend(matching_words)
                else:
                    pool.extend([f"{key}{key}", f"{key}", f"x{key}y"])

        if not pool:
            return self.get_passage("general", word_count=word_count)

        selected = [random.choice(pool) for _ in range(word_count)]
        return " ".join(selected)