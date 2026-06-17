import random
from typing import Any


MIXTURE_DIMENSIONS = ("source", "domain", "language", "quality_level")


def quality_level(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def sample_mixture(
    records: list[dict[str, Any]],
    ratios: dict[str, dict[str, float]],
    sample_size: int,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Sample records without replacement using metadata-based mixture weights."""
    weighted_records: list[tuple[dict[str, Any], float]] = []
    for record in records:
        metadata = record.get("metadata", {})
        values = {
            "source": str(metadata.get("source", record.get("source_id", "default"))),
            "domain": str(metadata.get("domain", "general")),
            "language": str(metadata.get("language", "unknown")),
            "quality_level": str(
                metadata.get(
                    "quality_level",
                    quality_level(float(record.get("quality_score", 0.0))),
                )
            ),
        }
        weight = 1.0
        for dimension in MIXTURE_DIMENSIONS:
            dimension_ratios = ratios.get(dimension, {})
            weight *= dimension_ratios.get(
                values[dimension], dimension_ratios.get("default", 1.0)
            )
        if weight > 0:
            enriched = {**record, "metadata": {**metadata, **values}}
            weighted_records.append((enriched, weight))

    randomizer = random.Random(seed)
    selected: list[dict[str, Any]] = []
    pool = weighted_records[:]
    target_size = min(max(sample_size, 0), len(pool))
    while pool and len(selected) < target_size:
        total_weight = sum(weight for _, weight in pool)
        choice = randomizer.random() * total_weight
        cumulative = 0.0
        for index, (record, weight) in enumerate(pool):
            cumulative += weight
            if choice <= cumulative:
                selected.append(record)
                pool.pop(index)
                break
    return selected
