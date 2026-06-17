import re
from collections import Counter

from src.cleaning import COMMON_PUNCTUATION, URL_PATTERN


WORD_PATTERN = re.compile(r"[\w]+", re.UNICODE)
SENTENCE_PATTERN = re.compile(r"[.!?。！？]+")
MOJIBAKE_PATTERN = re.compile(r"(?:Ã.|Â.|â.|ï¿½)")


def _clamp(value: float) -> float:
    return max(0.0, min(value, 1.0))


def _repeated_ngram_ratio(words: list[str], n: int = 2) -> float:
    if len(words) < n:
        return 0.0
    ngrams = [tuple(words[index : index + n]) for index in range(len(words) - n + 1)]
    unique_count = len(set(ngrams))
    return 1.0 - unique_count / len(ngrams)


def score_text(text: str) -> dict[str, float]:
    """Return explainable, heuristic quality scores in the 0-1 range."""
    compact = [character for character in text if not character.isspace()]
    compact_length = len(compact)
    words = WORD_PATTERN.findall(text.lower())

    length_score = _clamp(len(text) / 300)

    sentence_count = max(1, len(SENTENCE_PATTERN.findall(text)))
    average_sentence_length = len(words) / sentence_count
    sentence_length_score = 1.0 - min(abs(average_sentence_length - 18) / 30, 1.0)
    word_length = sum(len(word) for word in words) / len(words) if words else 0.0
    word_length_score = 1.0 - min(abs(word_length - 5) / 8, 1.0)
    readability_score = _clamp(0.6 * sentence_length_score + 0.4 * word_length_score)

    unique_word_ratio = len(set(words)) / len(words) if words else 0.0
    number_bonus = min(len(re.findall(r"\d+", text)) / 3, 1.0)
    structure_bonus = min(len(SENTENCE_PATTERN.findall(text)) / 3, 1.0)
    capitalized_bonus = min(len(re.findall(r"\b[A-Z][a-z]+\b", text)) / 3, 1.0)
    word_count_score = min(len(words) / 40, 1.0)
    informativeness_score = _clamp(
        0.4 * word_count_score
        + 0.3 * unique_word_ratio
        + 0.1 * number_bonus
        + 0.1 * structure_bonus
        + 0.1 * capitalized_bonus
    )

    if compact_length:
        garbled_count = sum(
            character == "\ufffd"
            or ord(character) < 32
            or 0xE000 <= ord(character) <= 0xF8FF
            for character in compact
        )
        garbled_count += len(MOJIBAKE_PATTERN.findall(text))
        special_count = sum(
            not character.isalnum() and character not in COMMON_PUNCTUATION
            for character in compact
        )
        url_char_count = sum(len(match.group(0)) for match in URL_PATTERN.finditer(text))
        garbled_ratio = garbled_count / compact_length
        special_ratio = special_count / compact_length
        url_ratio = min(url_char_count / compact_length, 1.0)
    else:
        garbled_ratio = special_ratio = url_ratio = 1.0
    noise_ratio = _clamp(0.45 * garbled_ratio + 0.35 * special_ratio + 0.2 * url_ratio)
    noise_score = 1.0 - noise_ratio

    repeated_ngram_ratio = _repeated_ngram_ratio(words)
    if compact:
        most_common_ratio = Counter(compact).most_common(1)[0][1] / compact_length
    else:
        most_common_ratio = 1.0
    repetition_score = 1.0 - _clamp(0.7 * repeated_ngram_ratio + 0.3 * most_common_ratio)

    final_quality_score = _clamp(
        0.15 * length_score
        + 0.2 * readability_score
        + 0.3 * informativeness_score
        + 0.2 * noise_score
        + 0.15 * repetition_score
    )

    return {
        "length_score": round(length_score, 4),
        "readability_score": round(readability_score, 4),
        "informativeness_score": round(informativeness_score, 4),
        "noise_score": round(noise_score, 4),
        "repetition_score": round(repetition_score, 4),
        "final_quality_score": round(final_quality_score, 4),
    }
