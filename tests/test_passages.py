"""Unit tests for PassageManager JSON integration, non-repetition, and targeted drills."""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from passages import PassageManager, DEFAULT_JSON_PATH


def test_passage_manager_json_source_of_truth(tmp_path):
    """Verify PassageManager reads custom passages from passages.json when available."""
    custom_data = {
        "general": ["alpha", "beta", "gamma"],
        "developer": ["print('custom_json_passage')"]
    }
    json_file = tmp_path / "passages.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(custom_data, f)

    pm = PassageManager(json_path=str(json_file))

    # Verify custom developer snippet loaded from JSON
    passage = pm.get_passage("developer")
    assert passage == "print('custom_json_passage')"


def test_anti_repetition_tracking():
    """Verify get_passage avoids serving the exact same snippet back-to-back when alternatives exist."""
    pm = PassageManager()

    # Request developer passage twice
    first = pm.get_passage("developer")
    second = pm.get_passage("developer")

    # If multiple templates exist in developer bank, consecutive picks shouldn't match
    if len(pm.passages.get("developer", [])) > 1:
        assert first != second


def test_targeted_symbol_drill_no_synthetic_tokens():
    """Verify symbol drills generate valid practice strings without dummy tokens."""
    pm = PassageManager()
    drill = pm.generate_targeted_exercise(["(", "[", "{", "_", "="], word_count=8)

    assert isinstance(drill, str)
    assert len(drill) > 0
    assert "key_" not in drill