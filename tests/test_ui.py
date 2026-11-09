"""User-visible Streamlit flows for the synthetic Promise Engine."""

import logging
import shutil
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def page_text(app):
    """Collect readable messages from the rendered page."""
    kinds = ("markdown", "subheader", "info", "warning", "success", "error", "caption")
    return "\n".join(str(element.value) for kind in kinds for element in getattr(app, kind))


class StreamlitUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context_logger = logging.getLogger(
            "streamlit.runtime.scriptrunner_utils.script_run_context"
        )
        cls.previous_log_level = cls.context_logger.level
        cls.context_logger.setLevel(logging.ERROR)

    @classmethod
    def tearDownClass(cls):
        cls.context_logger.setLevel(cls.previous_log_level)

    def setUp(self):
        self.directory = (ROOT / ".tmp" / f"ui-test-{uuid4().hex}").resolve()
        self.assertTrue(self.directory.is_relative_to((ROOT / ".tmp").resolve()))
        self.directory.mkdir()
        self.addCleanup(shutil.rmtree, self.directory)
        patched_dir = patch("ui.model_store.DEFAULT_DIR", self.directory)
        patched_dir.start()
        self.addCleanup(patched_dir.stop)

    def open_app(self):
        return AppTest.from_file(str(ROOT / "ui" / "app.py")).run(timeout=30)

    def test_page_shows_three_tabs_and_rule_scenarios(self):
        app = self.open_app()

        self.assertFalse(app.exception)
        self.assertEqual(
            [tab.label for tab in app.tabs],
            ["Sample scenarios", "Evaluate a request", "ML training"],
        )
        self.assertIn("REQ-001", page_text(app))
        self.assertIn("PROMISE", page_text(app))

    def test_ml_modes_prompt_for_training_without_saved_models(self):
        app = self.open_app()
        app.radio(key="sample_mode").set_value("ML").run()
        app.selectbox(key="evaluate_mode").set_value("ML").run()
        app.button(key="evaluate_submit").click().run()

        self.assertFalse(app.exception)
        self.assertIn("Train models in the ML training tab", page_text(app))

    def test_custom_infeasible_request_explains_missing_probabilities(self):
        app = self.open_app()
        app.number_input(key="quantity").set_value(10000).run()
        app.button(key="evaluate_submit").click().run()

        self.assertFalse(app.exception)
        self.assertIn("No feasible single source", page_text(app))
        self.assertIn("Probabilities are unavailable", page_text(app))

    def test_date_widget_prevents_past_sample_dates(self):
        app = self.open_app()
        app.date_input(key="delivery_date").set_value(date(2026, 11, 4))
        app.button(key="evaluate_submit").click().run()

        self.assertFalse(app.exception)
        self.assertGreaterEqual(app.date_input(key="delivery_date").value, date(2026, 11, 5))

    def test_train_and_reload_models_for_ml_evaluation(self):
        app = self.open_app()
        app.number_input(key="train_c").set_value(0.5)
        app.button(key="train_submit").click().run()

        self.assertFalse(app.exception)
        self.assertTrue((self.directory / "latest.skops").exists())
        self.assertIn("Training complete", page_text(app))
        self.assertIn("Latest saved model: C = 0.5", page_text(app))
        self.assertNotIn("No saved models yet", page_text(app))
        self.assertEqual(app.progress[0].value, 100)

        with patch("promise_poc.ml.train_models", side_effect=AssertionError("retrained")):
            reloaded = self.open_app()
            reloaded.selectbox(key="evaluate_mode").set_value("ML").run()
            reloaded.button(key="evaluate_submit").click().run()

        self.assertFalse(reloaded.exception)
        self.assertIn("REJECT", page_text(reloaded))
        self.assertIn("C = 0.5", page_text(reloaded))


if __name__ == "__main__":
    unittest.main()
