"""Load the bundled synthetic business records by category."""

import json
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SAMPLE_PATH = DATA_DIR
CATEGORIES = (
    "products",
    "locations",
    "lanes",
    "snapshots",
    "events",
    "counts",
    "orders",
    "demo_requests",
)
MAX_CATEGORY_BYTES = 20 * 1024 * 1024


def load_sample_data() -> dict[str, Any]:
    """Return the bundled, synthetic data with bounded category files."""
    base = DATA_DIR.resolve()
    data: dict[str, Any] = {}
    for category in ("metadata", *CATEGORIES):
        path = (base / f"{category}.json").resolve()
        if not path.is_relative_to(base):
            raise ValueError(f"Invalid sample path for {category}")
        if path.stat().st_size > MAX_CATEGORY_BYTES:
            raise ValueError(f"Sample category is too large: {category}")
        with path.open(encoding="utf-8") as sample_file:
            content = json.load(sample_file)
        if category == "metadata":
            if not isinstance(content, dict) or not isinstance(content.get("reference_time"), str):
                raise ValueError("Invalid sample metadata")
            data["reference_time"] = content["reference_time"]
        else:
            if (
                not isinstance(content, list)
                or len(content) > 20000
                or any(not isinstance(item, dict) for item in content)
            ):
                raise ValueError(f"Invalid sample category: {category}")
            data[category] = content
    return data
