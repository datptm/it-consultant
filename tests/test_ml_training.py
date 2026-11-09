"""Training controls for the synthetic classifiers."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from promise_poc.data import load_sample_data  # noqa: E402
from promise_poc.ml import TrainingConfig, train_models  # noqa: E402


class TrainingConfigTests(unittest.TestCase):
    def test_configured_training_applies_to_all_models_and_reports_progress(self):
        updates = []

        models = train_models(
            load_sample_data(),
            config=TrainingConfig(c=0.5, max_iter=200),
            progress=lambda kind, completed, total: updates.append((kind, completed, total)),
        )

        self.assertEqual(set(models), {"inventory", "fulfillment", "delivery"})
        self.assertEqual([model[-1].C for model in models.values()], [0.5] * 3)
        self.assertEqual([model[-1].max_iter for model in models.values()], [200] * 3)
        self.assertEqual(
            updates,
            [("inventory", 1, 3), ("fulfillment", 2, 3), ("delivery", 3, 3)],
        )

    def test_config_rejects_out_of_range_values(self):
        for kwargs in ({"c": 0}, {"c": 101}, {"max_iter": 99}, {"max_iter": 5001}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                TrainingConfig(**kwargs)


if __name__ == "__main__":
    unittest.main()
