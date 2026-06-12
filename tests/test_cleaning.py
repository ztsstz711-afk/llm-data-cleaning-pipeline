import unittest

from src.cleaning import (
    calculate_quality,
    get_filter_reason,
    normalize_text,
    text_hash,
)


DEFAULT_RULES = {
    "min_length": 20,
    "max_length": 5000,
    "max_url_count": 2,
    "max_special_char_ratio": 0.3,
    "max_repeated_char_ratio": 0.5,
    "min_valid_char_ratio": 0.5,
}


class CleaningTests(unittest.TestCase):
    def get_reason(self, text: str) -> str | None:
        return get_filter_reason(text, **DEFAULT_RULES)

    def test_normalize_text_strips_and_compresses_spaces(self) -> None:
        text = "   A   document\twith    extra spaces.   "
        self.assertEqual(normalize_text(text), "A document with extra spaces.")

    def test_too_short(self) -> None:
        self.assertEqual(self.get_reason("Short text."), "too_short")

    def test_too_many_urls(self) -> None:
        text = (
            "Read https://example.com/a https://example.com/b "
            "https://example.com/c for more information."
        )
        self.assertEqual(self.get_reason(text), "too_many_urls")

    def test_high_special_char_ratio(self) -> None:
        text = "Useful words @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ remain here."
        self.assertEqual(self.get_reason(text), "high_special_char_ratio")

    def test_high_repeated_char_ratio(self) -> None:
        text = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa normal words here"
        self.assertEqual(self.get_reason(text), "high_repeated_char_ratio")

    def test_low_valid_char_ratio(self) -> None:
        text = "Text: ,.!?;:,.!?;:,.!?;:,.!?;:,.!?;:,.!?;:"
        self.assertEqual(self.get_reason(text), "low_valid_char_ratio")

    def test_same_text_has_same_hash(self) -> None:
        text = "A reproducible document hash."
        self.assertEqual(text_hash(text), text_hash(text))

    def test_quality_score_is_between_zero_and_one(self) -> None:
        score, details = calculate_quality(
            "A clear document with enough useful text for quality scoring."
        )
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertIn("length_score", details)


if __name__ == "__main__":
    unittest.main()

