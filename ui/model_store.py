"""Save and load the latest locally trained demonstration models."""

import hashlib
import math
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

import sklearn
import skops.io
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from promise_poc.data import CATEGORIES
from promise_poc.ml import TrainingConfig

DEFAULT_DIR = Path(__file__).resolve().parent / ".local"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAX_MODEL_BYTES = 10 * 1024 * 1024
MODEL_KINDS = {"inventory", "fulfillment", "delivery"}


class ModelStoreError(ValueError):
    """A saved model cannot be used for this PoC."""


@dataclass(frozen=True)
class SavedModels:
    """The fitted pipelines and settings from the last successful training run."""

    models: dict[str, Any]
    config: TrainingConfig
    trained_at: str
    report: dict[str, Any] | None = None


class ModelStore:
    """Manage one fixed local artifact; callers provide only a trusted base directory."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = (directory if directory is not None else DEFAULT_DIR).resolve()
        if not self.directory.is_relative_to(PROJECT_ROOT):
            raise ModelStoreError("Model directory must stay inside the project")
        self.path = (self.directory / "latest.skops").resolve()
        if not self.path.is_relative_to(self.directory):
            raise ModelStoreError("Model path must stay inside its local directory")

    def save(
        self,
        models: dict[str, Any],
        config: TrainingConfig,
        sample_path: Path,
        report: dict[str, Any] | None = None,
    ) -> None:
        """Publish a complete bundle after all three models have trained."""
        _validate_models(models)
        _validate_report(report)
        bundle = {
            "format_version": 1,
            "models": models,
            "config": asdict(config),
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "sample_sha256": _sample_sha256(sample_path),
            "sklearn_version": sklearn.__version__,
            "report": report,
        }
        try:
            content = skops.io.dumps(bundle)
            if len(content) > MAX_MODEL_BYTES:
                raise ModelStoreError("Trained model exceeds the local size limit")
            self.directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=self.directory, suffix=".tmp", delete=False
            ) as temp:
                temp.write(content)
                temp_path = Path(temp.name)
            try:
                os.replace(temp_path, self.path)
            finally:
                temp_path.unlink(missing_ok=True)
        except OSError as error:
            raise ModelStoreError("Could not save the trained model locally") from error

    def load(self, sample_path: Path) -> SavedModels | None:
        """Load the latest bundle without training or trusting unknown types."""
        if not self.path.exists():
            return None
        try:
            if self.path.stat().st_size > MAX_MODEL_BYTES:
                raise ModelStoreError("Saved model is too large. Retrain in ML training.")
            with ZipFile(self.path) as archive:
                members = archive.infolist()
                if len(members) > 256 or sum(item.file_size for item in members) > MAX_MODEL_BYTES:
                    raise ModelStoreError("Saved model is too large. Retrain in ML training.")
        except (BadZipFile, OSError) as error:
            raise ModelStoreError("Saved model cannot be read. Retrain in ML training.") from error
        try:
            bundle = skops.io.load(self.path, trusted=[])
        except Exception as error:
            raise ModelStoreError(
                "Saved model cannot be loaded. Retrain in ML training."
            ) from error
        try:
            if not isinstance(bundle, dict) or bundle.get("format_version") != 1:
                raise ValueError("Unknown model format")
            if bundle["sklearn_version"] != sklearn.__version__:
                raise ValueError("scikit-learn version changed")
            if bundle["sample_sha256"] != _sample_sha256(sample_path):
                raise ValueError("Bundled sample changed")
            config = TrainingConfig(**bundle["config"])
            models = bundle["models"]
            _validate_models(models)
            trained_at = bundle["trained_at"]
            datetime.fromisoformat(trained_at)
            report = bundle.get("report")
            _validate_report(report)
        except (KeyError, TypeError, ValueError) as error:
            raise ModelStoreError("Saved model is incompatible. Retrain in ML training.") from error
        return SavedModels(models=models, config=config, trained_at=trained_at, report=report)


def _sample_sha256(sample_path: Path) -> str:
    path = sample_path.resolve()
    if not path.is_relative_to(PROJECT_ROOT):
        raise ModelStoreError("Sample path must stay inside the project")
    digest = hashlib.sha256()
    paths = (
        [path / f"{category}.json" for category in ("metadata", *CATEGORIES)]
        if path.is_dir()
        else [path]
    )
    for category_path in paths:
        resolved = category_path.resolve()
        if not resolved.is_relative_to(path if path.is_dir() else PROJECT_ROOT):
            raise ModelStoreError("Sample category must stay inside its directory")
        if resolved.stat().st_size > 20 * 1024 * 1024:
            raise ModelStoreError("Sample category is too large")
        digest.update(resolved.name.encode("utf-8"))
        digest.update(resolved.read_bytes())
    return digest.hexdigest()


def _validate_models(models: Any) -> None:
    if not isinstance(models, dict) or set(models) != MODEL_KINDS:
        raise ModelStoreError("A saved bundle must contain all three models")
    for model in models.values():
        if not isinstance(model, Pipeline) or len(model.steps) != 3:
            raise ModelStoreError("Unexpected saved model pipeline")
        if not isinstance(model.steps[0][1], DictVectorizer):
            raise ModelStoreError("Unexpected feature vectorizer")
        if not isinstance(model.steps[1][1], StandardScaler):
            raise ModelStoreError("Unexpected feature scaler")
        if not isinstance(model.steps[2][1], LogisticRegression):
            raise ModelStoreError("Unexpected classifier")


def _validate_report(report: Any) -> None:
    if report is None:
        return
    if not isinstance(report, dict) or set(report) != MODEL_KINDS:
        raise ModelStoreError("Invalid training report")
    count_keys = {"total_rows", "train_rows", "validation_rows", "test_rows"}
    time_keys = {"train_until", "validation_from", "validation_until", "test_from"}
    for result in report.values():
        if not isinstance(result, dict) or set(result) != count_keys | time_keys | {
            "validation",
            "test",
        }:
            raise ModelStoreError("Invalid training report")
        if any(type(result[key]) is not int or result[key] <= 0 for key in count_keys):
            raise ModelStoreError("Invalid training report counts")
        if sum(result[key] for key in count_keys - {"total_rows"}) != result["total_rows"]:
            raise ModelStoreError("Invalid training report counts")
        try:
            times = [datetime.fromisoformat(result[key]) for key in time_keys]
        except (TypeError, ValueError) as error:
            raise ModelStoreError("Invalid training report times") from error
        if any(time.tzinfo is None for time in times):
            raise ModelStoreError("Invalid training report times")
        for split in ("validation", "test"):
            scores = result[split]
            if not isinstance(scores, dict) or set(scores) != {"accuracy", "precision", "recall"}:
                raise ModelStoreError("Invalid training report scores")
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0 <= value <= 1
                for value in scores.values()
            ):
                raise ModelStoreError("Invalid training report scores")
