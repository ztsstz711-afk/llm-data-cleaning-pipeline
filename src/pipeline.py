from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from time import perf_counter

from src.cleaning import (
    calculate_quality,
    get_filter_reason,
    normalize_text,
    text_hash,
)
from src.jsonl_io import read_jsonl, write_json, write_jsonl
from src.summary import write_summary


def run_pipeline(
    input_path: Path,
    output_dir: Path,
    config_path: Path,
    config: dict[str, int | float],
) -> dict:
    started_at = datetime.now(timezone.utc)
    timer = perf_counter()
    filter_reason_counts: Counter[str] = Counter()
    invalid_record_counts = {
        "invalid_json": 0,
        "missing_text": 0,
        "invalid_text_type": 0,
    }
    seen_hashes: set[str] = set()
    cleaned_records: list[dict] = []
    total_records = 0
    valid_records = 0
    duplicate_records = 0

    for _, record, validation_error in read_jsonl(input_path):
        total_records += 1
        if validation_error:
            invalid_reason = (
                "invalid_text_type"
                if validation_error == "text_not_string"
                else validation_error
            )
            invalid_record_counts[invalid_reason] += 1
            continue

        valid_records += 1
        normalized_text = normalize_text(record["text"])
        filter_reason = get_filter_reason(
            normalized_text,
            int(config["min_length"]),
            int(config["max_length"]),
            int(config["max_url_count"]),
            float(config["max_special_char_ratio"]),
            float(config["max_repeated_char_ratio"]),
            float(config["min_valid_char_ratio"]),
        )
        if filter_reason:
            filter_reason_counts[filter_reason] += 1
            continue

        fingerprint = text_hash(normalized_text)
        if fingerprint in seen_hashes:
            duplicate_records += 1
            continue
        seen_hashes.add(fingerprint)

        quality_score, quality_details = calculate_quality(normalized_text)
        if quality_score < config["quality_threshold"]:
            filter_reason_counts["low_quality"] += 1
            continue

        cleaned_records.append(
            {
                "text": normalized_text,
                "quality_score": quality_score,
                "quality_details": quality_details,
            }
        )

    cleaned_path = output_dir / "cleaned.jsonl"
    report_path = output_dir / "report.json"
    summary_path = output_dir / "summary.md"
    scores = [record["quality_score"] for record in cleaned_records]
    kept_records = len(cleaned_records)
    removed_records = total_records - kept_records
    report = {
        "input_path": str(input_path),
        "output_path": str(cleaned_path),
        "config_path": str(config_path),
        "started_at_utc": started_at.isoformat(),
        "processing_time_seconds": round(perf_counter() - timer, 4),
        "settings": {
            "min_length": config["min_length"],
            "max_length": config["max_length"],
            "quality_threshold": config["quality_threshold"],
            "max_url_count": config["max_url_count"],
            "max_special_char_ratio": config["max_special_char_ratio"],
            "max_repeated_char_ratio": config["max_repeated_char_ratio"],
            "min_valid_char_ratio": config["min_valid_char_ratio"],
            "deduplication": "sha256_exact_match",
        },
        "total_records": total_records,
        "valid_records": valid_records,
        "kept_records": kept_records,
        "removed_records": removed_records,
        "keep_ratio": round(kept_records / total_records, 4) if total_records else 0.0,
        "remove_ratio": round(removed_records / total_records, 4) if total_records else 0.0,
        "invalid_record_counts": invalid_record_counts,
        "filter_reason_counts": dict(sorted(filter_reason_counts.items())),
        "duplicate_records": duplicate_records,
        "quality_score_summary": {
            "min": min(scores) if scores else None,
            "max": max(scores) if scores else None,
            "mean": round(sum(scores) / len(scores), 4) if scores else None,
            "median": round(median(scores), 4) if scores else None,
        },
    }

    write_jsonl(cleaned_path, cleaned_records)
    write_json(report_path, report)
    write_summary(summary_path, report)
    return report
