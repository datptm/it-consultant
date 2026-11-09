"""Three independent toy classifiers trained afresh from bundled history."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import build_training_examples, build_training_rows


@dataclass(frozen=True)
class TrainingConfig:
    """Shared training settings for the three demonstration classifiers."""

    c: float = 1.0
    max_iter: int = 1000

    def __post_init__(self) -> None:
        if (
            isinstance(self.c, bool)
            or not isinstance(self.c, (int, float))
            or not 0.01 <= self.c <= 100
        ):
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
        model = _new_model(config)
        model.fit([features for features, _ in rows], labels)
        models[kind] = model
        if progress is not None:
            progress(kind, completed, len(kinds))
    return models


def train_models_with_report(
    data: dict[str, Any],
    config: TrainingConfig | None = None,
    progress: Callable[[str, int, int], None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fit on the earliest 70% of each history and score later validation/test rows."""
    config = config or TrainingConfig()
    models: dict[str, Any] = {}
    reports: dict[str, Any] = {}
    kinds = ("inventory", "fulfillment", "delivery")
    for completed, kind in enumerate(kinds, start=1):
        examples = sorted(build_training_examples(data, kind), key=lambda row: row[2])
        total = len(examples)
        train_end = int(total * 0.70)
        validation_end = int(total * 0.85)
        train = examples[:train_end]
        validation = examples[train_end:validation_end]
        test = examples[validation_end:]
        if not train or not validation or not test:
            raise ValueError(f"{kind} needs rows in all three time splits")
        if len({label for _, label, _ in train}) != 2:
            raise ValueError(f"{kind} training split needs both positive and negative examples")
        model = _new_model(config)
        model.fit([features for features, _, _ in train], [label for _, label, _ in train])
        models[kind] = model
        reports[kind] = {
            "total_rows": total,
            "train_rows": len(train),
            "validation_rows": len(validation),
            "test_rows": len(test),
            "train_until": train[-1][2].isoformat(),
            "validation_from": validation[0][2].isoformat(),
            "validation_until": validation[-1][2].isoformat(),
            "test_from": test[0][2].isoformat(),
            "validation": _classification_scores(model, validation),
            "test": _classification_scores(model, test),
        }
        if progress is not None:
            progress(kind, completed, len(kinds))
    return models, reports


def _new_model(config: TrainingConfig) -> Any:
    return make_pipeline(
        DictVectorizer(),
        StandardScaler(with_mean=False),
        LogisticRegression(C=config.c, max_iter=config.max_iter),
    )


def _classification_scores(
    model: Any, examples: list[tuple[dict[str, float | int | str], int, datetime]]
) -> dict[str, float]:
    labels = [label for _, label, _ in examples]
    predictions = model.predict([features for features, _, _ in examples])
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
    }


def predict_success(model: Any, features: dict[str, float | int | str]) -> float:
    """Return the classifier probability for the positive outcome."""
    positive_index = list(model.classes_).index(1)
    return float(model.predict_proba([features])[0][positive_index])
