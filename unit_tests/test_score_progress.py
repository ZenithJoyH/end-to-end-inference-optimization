import pickle
import sqlite3
import tempfile
import unittest
from pathlib import Path

from score_progress import read_scores, strict_extract


class ScoreProgressTests(unittest.TestCase):
    def test_terminal_letter_is_not_lost(self):
        self.assertEqual(strict_extract("The best answer is D"), "D")
        self.assertEqual(strict_extract("The best answer is (B)"), "B")

    def test_last_native_match_is_selected(self):
        response = "The answer is A. After checking, the best answer is C"
        self.assertEqual(strict_extract(response), "C")

    def test_bold_letter_is_not_extra_native_support(self):
        self.assertEqual(strict_extract("The best answer is **B**."), "[invalid]")

    def test_cache_progress_counts_terminal_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "responses.db"
            connection = sqlite3.connect(cache)
            connection.execute("CREATE TABLE unnamed (key TEXT, value BLOB)")
            connection.execute(
                "INSERT INTO unnamed VALUES (?, ?)",
                ("sample", pickle.dumps("The best answer is C")),
            )
            connection.commit()
            connection.close()
            scores = read_scores(
                cache, {"sample": {"target": "C", "choices": ["x", "y", "z", "w"]}}
            )
            self.assertEqual(scores["completed"], 1)
            self.assertEqual(scores["matched"], 1)
            self.assertEqual(scores["strict"], 1)


if __name__ == "__main__":
    unittest.main()
