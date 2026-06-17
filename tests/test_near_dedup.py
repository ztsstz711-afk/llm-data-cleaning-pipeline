import unittest

from src.near_dedup import (
    hamming_distance,
    is_near_duplicate,
    simhash,
    tokenize_text,
)


class NearDedupTests(unittest.TestCase):
    def test_tokenize_text_handles_english_and_chinese(self) -> None:
        self.assertEqual(
            tokenize_text("Data 清洗 Pipeline"),
            ["data", "清", "洗", "pipeline"],
        )

    def test_different_text_is_not_near_duplicate(self) -> None:
        existing = [simhash("Python memory management uses reference counting.")]
        text = "Fresh vegetables need sunlight, water, and healthy soil."
        self.assertFalse(is_near_duplicate(text, existing, threshold=3))

    def test_similar_text_is_near_duplicate(self) -> None:
        original = "Large language models require clean and diverse training data."
        similar = "Large language models require clean, diverse training data."
        existing = [simhash(original)]
        self.assertTrue(is_near_duplicate(similar, existing, threshold=8))

    def test_threshold_controls_strictness(self) -> None:
        original = "Retrieval augmented generation uses retrieved context."
        similar = "Retrieval augmented generation uses relevant retrieved context."
        distance = hamming_distance(simhash(original), simhash(similar))
        existing = [simhash(original)]
        self.assertFalse(is_near_duplicate(similar, existing, threshold=distance - 1))
        self.assertTrue(is_near_duplicate(similar, existing, threshold=distance))

    def test_simhash_is_stable_for_same_text(self) -> None:
        text = "Stable fingerprints are important for reproducible deduplication."
        self.assertEqual(simhash(text), simhash(text))


if __name__ == "__main__":
    unittest.main()

