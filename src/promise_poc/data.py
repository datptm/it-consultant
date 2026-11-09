"""Load the bundled synthetic business records."""

import json
from pathlib import Path
from typing import Any


SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "sample.json"


def load_sample_data() -> dict[str, Any]:
    """Return the bundled, synthetic data without modifying it."""
    with SAMPLE_PATH.open(encoding="utf-8") as sample_file:
        return json.load(sample_file)
