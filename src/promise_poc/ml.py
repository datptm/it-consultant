"""Three independent toy classifiers trained afresh from bundled history."""

from dataclasses import dataclass
from typing import Any, Callable

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from .features import build_training_rows


@dataclass(frozen=True)
class TrainingConfig:
    """Shared training settings for the three demonstration classifiers."""

    c: float = 1.0
    max_iter: int = 1000

    def __post_init__(self) -> None:
        if isinstance(self.c, bool) or not isinstance(self.c, (int, float)) or not 0.01 <= self.c <= 100:
            raise ValueError("C must be between 0.01 and 100")
        if type(self.max_iter) is not int or not 100 <= self.max_iter <= 5000:
            raise ValueError("max_iter must be an integer between 100 and 5000")


def train_models(
    data: dict[str, Any],
    config: TrainingConfig | None = None,
    progress: Callable[[str, int, int], None] | None = None,
) -> dict[str, Any]:
    """Fit inventory, fulfillment and delivery classifiers in memory."""
    config = config or TrainingConfig()
    models: dict[str, Any] = {}
    kinds = ("inventory", "fulfillment", "delivery")
    for completed, kind in enumerate(kinds, start=1):
        rows = build_training_rows(data, kind)
        labels = [label for _, label in rows]
        if len(set(labels)) != 2:
            raise ValueError(f"{kind} needs both positive and negative examples")
        model = make_pipeline(
            DictVectorizer(), LogisticRegression(C=config.c, max_iter=config.max_iter)
        )
        model.fit([features for features, _ in rows], labels)
        models[kind] = model
        if progress is not None:
            progress(kind, completed, len(kinds))
    return models


def predict_success(model: Any, features: dict[str, float | int | str]) -> float:
    """Return the classifier probability for the positive outcome."""
    positive_index = list(model.classes_).index(1)
    return float(model.predict_proba([features])[0][positive_index])
