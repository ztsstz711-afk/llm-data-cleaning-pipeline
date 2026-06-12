import hashlib
import re
from collections import Counter


URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
COMMON_PUNCTUATION = set(".,!?;:'\"-()[]{}，。！？；：、“”‘’（）【】《》…")


def normalize_text(text: str) -> str:
    """Apply small, predictable normalization rules without changing content."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_text_ratios(text: str) -> tuple[float, float, float]:
    compact_text = [character for character in text if not character.isspace()]
    compact_length = len(compact_text)
    if not compact_text:
        return 0.0, 0.0, 1.0

    valid_count = sum(character.isalnum() for character in compact_text)
    special_count = sum(
        not character.isalnum() and character not in COMMON_PUNCTUATION
        for character in compact_text
    )
    most_common_count = Counter(compact_text).most_common(1)[0][1]

    return (
        valid_count / compact_length,
        special_count / compact_length,
        most_common_count / compact_length,
    )


def get_filter_reason(
    text: str,
    min_length: int,
    max_length: int,
    max_url_count: int,
    max_special_char_ratio: float,
    max_repeated_char_ratio: float,
    min_valid_char_ratio: float,
) -> str | None:
    if not text:
        return "empty_text"
    if len(text) < min_length:
        return "too_short"
    if len(text) > max_length:
        return "too_long"

    if len(URL_PATTERN.findall(text)) > max_url_count:
        return "too_many_urls"

    valid_ratio, special_ratio, repeated_ratio = get_text_ratios(text)
    if special_ratio > max_special_char_ratio:
        return "high_special_char_ratio"
    if repeated_ratio > max_repeated_char_ratio:
        return "high_repeated_char_ratio"
    if valid_ratio < min_valid_char_ratio:
        return "low_valid_char_ratio"
    return None


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def calculate_quality(text: str) -> tuple[float, dict[str, float]]:
    """Return a 0-1 score and its three explainable components."""
    length_score = min(len(text) / 200, 1.0)
    valid_character_ratio, _, repeated_character_ratio = get_text_ratios(text)
    repetition_score = 1.0 - repeated_character_ratio

    score = (
        0.4 * length_score
        + 0.35 * valid_character_ratio
        + 0.25 * repetition_score
    )
    details = {
        "length_score": round(length_score, 4),
        "valid_character_ratio": round(valid_character_ratio, 4),
        "repeated_character_ratio": round(repeated_character_ratio, 4),
    }
    return round(max(0.0, min(score, 1.0)), 4), details
