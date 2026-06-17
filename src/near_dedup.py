import hashlib
import re


TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9]+", re.UNICODE)


def tokenize_text(text: str) -> list[str]:
    """Tokenize English-like words and Chinese characters for simple SimHash."""
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def simhash(text: str, num_bits: int = 64) -> int:
    tokens = tokenize_text(text)
    if not tokens:
        return 0

    weights = [0] * num_bits
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        value = int.from_bytes(digest, byteorder="big")
        for bit_index in range(num_bits):
            bit = (value >> bit_index) & 1
            weights[bit_index] += 1 if bit else -1

    fingerprint = 0
    for bit_index, weight in enumerate(weights):
        if weight >= 0:
            fingerprint |= 1 << bit_index
    return fingerprint


def hamming_distance(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def is_near_duplicate(
    text: str,
    existing_fingerprints: list[int],
    threshold: int = 3,
    num_bits: int = 64,
) -> bool:
    fingerprint = simhash(text, num_bits=num_bits)
    return any(
        hamming_distance(fingerprint, existing) <= threshold
        for existing in existing_fingerprints
    )
