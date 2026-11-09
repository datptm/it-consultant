"""Save and load the latest locally trained demonstration models."""

import hashlib
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


class ModelStore:
    """Manage one fixed local artifact; callers provide only a trusted base directory."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = (directory if directory is not None else DEFAULT_DIR).resolve()
        if not self.directory.is_relative_to(PROJECT_ROOT):
            raise ModelStoreError("Model directory must stay inside the project")
        self.path = (self.directory / "latest.skops").resolve()
        if not self.path.is_relative_to(self.directory):
            raise ModelStoreError("Model path must stay inside its local directory")

    def save(self, models: dict[str, Any], config: TrainingConfig, sample_path: Path) -> None:
        """Publish a complete bundle after all three models have trained."""
        _validate_models(models)
        bundle = {
            "format_version": 1,
            "models": models,
            "config": asdict(config),
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "sample_sha256": _sample_sha256(sample_path),
            "sklearn_version": sklearn.__version__,
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
        except (KeyError, TypeError, ValueError) as error:
            raise ModelStoreError("Saved model is incompatible. Retrain in ML training.") from error
        return SavedModels(models=models, config=config, trained_at=trained_at)


def _sample_sha256(sample_path: Path) -> str:
    return hashlib.sha256(sample_path.read_bytes()).hexdigest()


def _validate_models(models: Any) -> None:
    if not isinstance(models, dict) or set(models) != MODEL_KINDS:
        raise ModelStoreError("A saved bundle must contain all three models")
    for model in models.values():
        if not isinstance(model, Pipeline) or len(model.steps) != 2:
            raise ModelStoreError("Unexpected saved model pipeline")
        if not isinstance(model.steps[0][1], DictVectorizer):
            raise ModelStoreError("Unexpected feature vectorizer")
        if not isinstance(model.steps[1][1], LogisticRegression):
            raise ModelStoreError("Unexpected classifier")
