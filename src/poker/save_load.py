"""Save and load game state to/from a text file."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SAVE_FILE = Path.home() / ".poker_save.json"


def save_game(data: dict[str, Any]) -> None:
    """Persist game state to the save file."""
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_game() -> dict[str, Any] | None:
    """Load game state. Returns None if no save exists."""
    if not SAVE_FILE.exists():
        return None
    try:
        with open(SAVE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return None


def delete_save() -> None:
    """Remove the save file."""
    if SAVE_FILE.exists():
        SAVE_FILE.unlink()


def has_save() -> bool:
    return SAVE_FILE.exists()


def save_path() -> str:
    return str(SAVE_FILE)
