"""Unit tests for PassageManager categories, JSON loading, and weak-key drill generation."""

import os
import pytest
from passages import PassageManager, DEFAULT_PASSAGES


def test_fallback_on_missing_file():
    pm = PassageManager("non_existent_file.json")
    assert "general" in pm.passages
    assert "developer" in pm.passages
    assert len(pm.passages["developer"]) > 0


def test_get_developer_passage():
    pm = PassageManager()
    passage = pm.get_passage("developer")
    assert isinstance(passage, str)
    assert len(passage) > 0


def test_targeted_drill_generation():
    pm = PassageManager()
    weak_keys = ["d", "e", "f"]
    drill = pm.generate_targeted_exercise(weak_keys, word_count=5)
    assert isinstance(drill, str)
    assert len(drill.split()) == 5