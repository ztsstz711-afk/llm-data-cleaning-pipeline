import unittest

from src.quality_scorer import score_text


class QualityScorerTests(unittest.TestCase):
    def test_scorer_returns_all_metrics_in_range(self) -> None:
        scores = score_text(
            "Python 3.13 provides language features for reliable data pipelines. "
            "This document explains the design with clear sentences."
        )
        expected_metrics = {
            "length_score",
            "readability_score",
            "informativeness_score",
            "noise_score",
            "repetition_score",
            "final_quality_score",
        }
        self.assertEqual(set(scores), expected_metrics)
        for score in scores.values():
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_repeated_ngrams_reduce_repetition_score(self) -> None:
        varied = score_text("data quality improves retrieval and model training results")
        repeated = score_text("data quality data quality data quality data quality")
        self.assertLess(repeated["repetition_score"], varied["repetition_score"])

    def test_noisy_text_reduces_noise_score(self) -> None:
        clean = score_text("A clean and readable sentence about model training data.")
        noisy = score_text("@@@@ #### https://a.example https://b.example \ufffd\ufffd\ufffd")
        self.assertLess(noisy["noise_score"], clean["noise_score"])


if __name__ == "__main__":
    unittest.main()

