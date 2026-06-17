from typing import Any

from src.quality_scorer import score_text


def build_chunks(
    records: list[dict[str, Any]],
    chunk_size: int,
    overlap: int,
    quality_threshold: float,
) -> list[dict[str, Any]]:
    """Split cleaned records into fixed-length overlapping RAG chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size - 1")

    chunks: list[dict[str, Any]] = []
    step = chunk_size - overlap
    for record_index, record in enumerate(records):
        text = record["text"]
        source_id = record.get("source_id", f"source-{record_index}")
        metadata = dict(record.get("metadata", {}))
        for chunk_index, start in enumerate(range(0, len(text), step)):
            chunk_text = text[start : start + chunk_size].strip()
            if not chunk_text:
                continue
            scores = score_text(chunk_text)
            quality_score = scores["final_quality_score"]
            if quality_score < quality_threshold:
                continue
            chunks.append(
                {
                    "source_id": source_id,
                    "chunk_id": f"{source_id}-chunk-{chunk_index}",
                    "text": chunk_text,
                    "quality_score": quality_score,
                    "metadata": {
                        **metadata,
                        "start_char": start,
                        "end_char": start + len(chunk_text),
                    },
                }
            )
            if start + chunk_size >= len(text):
                break
    return chunks

