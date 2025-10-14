from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).resolve().parent / "data" / "songs.json"


def load_songs() -> list[dict[str, Any]]:
    """Load song metadata and lyrics from bundled JSON."""
    with _DATA_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data
