"""Training controls for the synthetic classifiers."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from promise_poc.data import load_sample_data  # noqa: E402
from promise_poc.features import build_training_examples  # noqa: E402
from promise_poc.ml import TrainingConfig, train_models, train_models_with_report  # noqa: E402


class TrainingConfigTests(unittest.TestCase):
    def test_report_uses_disjoint_chronological_splits_and_bounded_scores(self):
        data = load_sample_data()
        models, reports = train_models_with_report(data)

        self.assertEqual(set(models), {"inventory", "fulfillment", "delivery"})
        self.assertEqual(set(reports), set(models))
        for kind, report in reports.items():
            with self.subTest(kind=kind):
                self.assertGreater(report["train_rows"], 0)
                self.assertGreater(report["validation_rows"], 0)
                self.assertGreater(report["test_rows"], 0)
                self.assertEqual(
                    report["train_rows"] + report["validation_rows"] + report["test_rows"],
                    report["total_rows"],
                )
                self.assertLessEqual(report["train_until"], report["validation_from"])
                self.assertLessEqual(report["validation_until"], report["test_from"])
                for split in ("validation", "test"):
                    for metric in ("accuracy", "precision", "recall"):
                        self.assertGreaterEqual(report[split][metric], 0.0)
                        self.assertLessEqual(report[split][metric], 1.0)
                examples = sorted(build_training_examples(data, kind), key=lambda row: row[2])
                test_examples = examples[-report["test_rows"] :]
                actual = [label for _, label, _ in test_examples]
                predicted = models[kind].predict([features for features, _, _ in test_examples])
                true_positive = sum(a == 1 and p == 1 for a, p in zip(actual, predicted))
                predicted_positive = sum(predicted)
                actual_positive = sum(actual)
                self.assertAlmostEqual(
                    report["test"]["accuracy"],
                    sum(a == p for a, p in zip(actual, predicted)) / len(actual),
                )
                self.assertAlmostEqual(
                    report["test"]["precision"],
                    true_positive / predicted_positive if predicted_positive else 0,
                )
                self.assertAlmostEqual(
                    report["test"]["recall"],
                    true_positive / actual_positive if actual_positive else 0,
                )

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
