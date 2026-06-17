import re
from typing import Any


def generate_qa_pairs(
    chunks: list[dict[str, Any]],
    min_quality: float,
    max_pairs_per_chunk: int = 1,
) -> list[dict[str, Any]]:
    """Generate deterministic template-based QA pairs without external APIs."""
    qa_pairs: list[dict[str, Any]] = []
    for chunk in chunks:
        if chunk["quality_score"] < min_quality:
            continue
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?。！？])\s*", chunk["text"])
            if sentence.strip()
        ]
        for pair_index, answer in enumerate(sentences[:max_pairs_per_chunk]):
            qa_pairs.append(
                {
                    "source_id": chunk["source_id"],
                    "chunk_id": chunk["chunk_id"],
                    "question": f"What information is provided in {chunk['chunk_id']}?",
                    "answer": answer,
                    "quality_score": chunk["quality_score"],
                    "metadata": {
                        **chunk.get("metadata", {}),
                        "generator": "template_demo",
                        "pair_index": pair_index,
                    },
                }
            )
    return qa_pairs

