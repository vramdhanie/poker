"""Tests for save_load.py — JSON persistence."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from poker.save_load import save_game, load_game, delete_save, has_save, save_path, SAVE_FILE


SAMPLE_DATA = {
    "player_name": "TestPlayer",
    "human_stack": 750,
    "human_wins": 3,
    "human_hands": 10,
    "ai_stacks": [1200, 800, 950],
    "ai_wins": [2, 1, 4],
    "hand_number": 10,
    "dealer_index": 2,
}


@pytest.fixture(autouse=True)
def cleanup_save():
    """Remove save file before and after every test."""
    if SAVE_FILE.exists():
        SAVE_FILE.unlink()
    yield
    if SAVE_FILE.exists():
        SAVE_FILE.unlink()


class TestSaveGame:
    def test_save_creates_file(self):
        save_game(SAMPLE_DATA)
        assert SAVE_FILE.exists()

    def test_save_writes_valid_json(self):
        save_game(SAMPLE_DATA)
        with open(SAVE_FILE) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_save_preserves_all_fields(self):
        save_game(SAMPLE_DATA)
        with open(SAVE_FILE) as f:
            data = json.load(f)
        for key, val in SAMPLE_DATA.items():
            assert data[key] == val

    def test_save_overwrites_existing(self):
        save_game(SAMPLE_DATA)
        updated = {**SAMPLE_DATA, "human_stack": 9999}
        save_game(updated)
        loaded = load_game()
        assert loaded["human_stack"] == 9999

    def test_save_path_is_in_home(self):
        assert str(SAVE_FILE).startswith(str(Path.home()))


class TestLoadGame:
    def test_load_returns_none_when_no_file(self):
        assert not SAVE_FILE.exists()
        result = load_game()
        assert result is None

    def test_load_returns_dict_after_save(self):
        save_game(SAMPLE_DATA)
        result = load_game()
        assert isinstance(result, dict)

    def test_load_returns_correct_values(self):
        save_game(SAMPLE_DATA)
        result = load_game()
        assert result["player_name"] == "TestPlayer"
        assert result["human_stack"] == 750
        assert result["ai_stacks"] == [1200, 800, 950]
        assert result["hand_number"] == 10

    def test_load_returns_none_on_corrupt_json(self):
        SAVE_FILE.write_text("not valid json {{")
        result = load_game()
        assert result is None

    def test_load_returns_none_on_empty_file(self):
        SAVE_FILE.write_text("")
        result = load_game()
        assert result is None


class TestDeleteSave:
    def test_delete_removes_file(self):
        save_game(SAMPLE_DATA)
        assert SAVE_FILE.exists()
        delete_save()
        assert not SAVE_FILE.exists()

    def test_delete_when_no_file_does_not_raise(self):
        assert not SAVE_FILE.exists()
        delete_save()  # should be a no-op


class TestHasSave:
    def test_has_save_false_when_no_file(self):
        assert not has_save()

    def test_has_save_true_after_save(self):
        save_game(SAMPLE_DATA)
        assert has_save()

    def test_has_save_false_after_delete(self):
        save_game(SAMPLE_DATA)
        delete_save()
        assert not has_save()


class TestSavePath:
    def test_save_path_returns_string(self):
        assert isinstance(save_path(), str)

    def test_save_path_ends_with_json(self):
        assert save_path().endswith(".json")

    def test_save_path_matches_save_file(self):
        assert save_path() == str(SAVE_FILE)


class TestRoundTrip:
    def test_save_then_load_is_identity(self):
        save_game(SAMPLE_DATA)
        loaded = load_game()
        assert loaded == SAMPLE_DATA

    def test_multiple_save_load_cycles(self):
        for i in range(5):
            data = {**SAMPLE_DATA, "hand_number": i}
            save_game(data)
            loaded = load_game()
            assert loaded["hand_number"] == i
