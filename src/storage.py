"""Persistence helpers for the inverted index."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_index(index_data: dict[str, Any], output_path: str | Path) -> None:
    """Write the full index structure to disk as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index_data, indent=2), encoding="utf-8")


def load_index(input_path: str | Path) -> dict[str, Any]:
    """Load previously saved index data from disk."""
    path = Path(input_path)
    return json.loads(path.read_text(encoding="utf-8"))
