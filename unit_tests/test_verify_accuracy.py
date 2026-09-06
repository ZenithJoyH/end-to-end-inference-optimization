import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "evaluation"
    / "accuracy"
    / "verify_accuracy.py"
)
SPEC = importlib.util.spec_from_file_location("verify_accuracy", MODULE_PATH)
VERIFY_ACCURACY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VERIFY_ACCURACY)


class MetricValueTest(unittest.TestCase):
    def test_exact_metric_name(self):
        self.assertEqual(VERIFY_ACCURACY.metric_value({"score": 0.5}, "score"), 0.5)

    def test_lm_eval_filter_suffix(self):
        self.assertEqual(
            VERIFY_ACCURACY.metric_value(
                {"exact_match,strict-match": 0.42}, "exact_match"
            ),
            0.42,
        )

    def test_ambiguous_metric_is_rejected(self):
        with self.assertRaises(ValueError):
            VERIFY_ACCURACY.metric_value(
                {
                    "exact_match,strict-match": 0.42,
                    "exact_match,flexible-extract": 0.50,
                },
                "exact_match",
            )

    def test_non_finite_metric_is_rejected(self):
        with self.assertRaises(ValueError):
            VERIFY_ACCURACY.metric_value({"score": float("nan")}, "score")


if __name__ == "__main__":
    unittest.main()
