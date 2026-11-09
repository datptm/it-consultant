"""Persisted synthetic models must remain reusable and fail closed."""

import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from promise_poc.data import SAMPLE_PATH, load_sample_data  # noqa: E402
from promise_poc.engine import evaluate  # noqa: E402
from promise_poc.ml import TrainingConfig, train_models  # noqa: E402
from ui.model_store import MAX_MODEL_BYTES, ModelStore, ModelStoreError  # noqa: E402


class ModelStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = (ROOT / ".tmp" / f"model-test-{uuid4().hex}").resolve()
        self.assertTrue(self.directory.is_relative_to((ROOT / ".tmp").resolve()))
        self.directory.mkdir()
        self.addCleanup(shutil.rmtree, self.directory)
        self.store = ModelStore(self.directory)

    def test_missing_model_requires_training(self):
        self.assertIsNone(self.store.load(SAMPLE_PATH))

    def test_model_directory_must_stay_inside_project(self):
        with self.assertRaises(ModelStoreError):
            ModelStore(ROOT.parent / "outside-model-dir")

    def test_saved_models_preserve_predictions_and_settings(self):
        data = load_sample_data()
        config = TrainingConfig(c=0.5, max_iter=200)
        models = train_models(data, config)
        expected = evaluate(data, data["demo_requests"][0], "ml", models)

        self.store.save(models, config, SAMPLE_PATH)
        saved = ModelStore(self.directory).load(SAMPLE_PATH)

        self.assertEqual(saved.config, config)
        self.assertEqual(evaluate(data, data["demo_requests"][0], "ml", saved.models), expected)
        self.assertIsNotNone(saved.trained_at)

    def test_corrupted_model_is_rejected(self):
        self.store.path.write_bytes(b"not a model")

        with self.assertRaises(ModelStoreError):
            self.store.load(SAMPLE_PATH)

    def test_compressed_oversized_model_is_rejected_before_loading(self):
        with ZipFile(self.store.path, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("huge", b"x" * (MAX_MODEL_BYTES + 1))

        with self.assertRaisesRegex(ModelStoreError, "too large"):
            self.store.load(SAMPLE_PATH)

    def test_incompatible_environment_requires_retraining(self):
        self.store.save(train_models(load_sample_data()), TrainingConfig(), SAMPLE_PATH)

        with patch("ui.model_store.sklearn.__version__", "0.0"):
            with self.assertRaisesRegex(ModelStoreError, "Retrain"):
                self.store.load(SAMPLE_PATH)

    def test_changed_sample_requires_retraining(self):
        self.store.save(train_models(load_sample_data()), TrainingConfig(), SAMPLE_PATH)
        other_sample = self.directory / "other.json"
        other_sample.write_text("{}", encoding="utf-8")

        with self.assertRaisesRegex(ModelStoreError, "Retrain"):
            self.store.load(other_sample)


if __name__ == "__main__":
    unittest.main()
