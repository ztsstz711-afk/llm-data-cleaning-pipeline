from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Any

from src.cleaning import (
    get_filter_reason,
    normalize_text,
    text_hash,
)
from src.data_mixer import sample_mixture
from src.jsonl_io import read_jsonl, write_json, write_jsonl
from src.llm_judge import LLMJudge
from src.quality_scorer import score_text
from src.rag_chunker import build_chunks
from src.summary import write_summary
from src.synthetic_qa import generate_qa_pairs


QUALITY_METRICS = (
    "length_score",
    "readability_score",
    "informativeness_score",
    "noise_score",
    "repetition_score",
    "final_quality_score",
)

MODULE_DEFAULTS: dict[str, int | float] = {
    "rag_chunk_size": 300,
    "rag_chunk_overlap": 50,
    "rag_chunk_quality_threshold": 0.0,
    "synthetic_qa_min_quality": 0.0,
    "synthetic_qa_max_pairs_per_chunk": 1,
    "mixture_sample_size": 100,
    "mixture_seed": 42,
    "mixture_source_default": 1.0,
    "mixture_domain_general": 1.0,
    "mixture_language_en": 1.0,
    "mixture_language_zh": 1.0,
    "mixture_language_unknown": 1.0,
    "mixture_quality_high": 1.5,
    "mixture_quality_medium": 1.0,
    "mixture_quality_low": 0.5,
}

JUDGE_DEFAULTS: dict[str, Any] = {
    "enabled": True,
    "mode": "heuristic",
    "quality_threshold": 3,
    "api_key_env": "OPENAI_API_KEY",
}


def _score_summary(values: list[float]) -> dict[str, float | None]:
    return {
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "mean": round(sum(values) / len(values), 4) if values else None,
        "median": round(median(values), 4) if values else None,
    }


def _detect_language(text: str) -> str:
    chinese_count = sum("\u4e00" <= character <= "\u9fff" for character in text)
    latin_count = sum(character.isascii() and character.isalpha() for character in text)
    if chinese_count > latin_count:
        return "zh"
    if latin_count:
        return "en"
    return "unknown"


def _mixture_ratios(config: dict[str, int | float]) -> dict[str, dict[str, float]]:
    return {
        "source": {"default": float(config["mixture_source_default"])},
        "domain": {"general": float(config["mixture_domain_general"])},
        "language": {
            "en": float(config["mixture_language_en"]),
            "zh": float(config["mixture_language_zh"]),
            "unknown": float(config["mixture_language_unknown"]),
        },
        "quality_level": {
            "high": float(config["mixture_quality_high"]),
            "medium": float(config["mixture_quality_medium"]),
            "low": float(config["mixture_quality_low"]),
        },
    }


def run_pipeline(
    input_path: Path,
    output_dir: Path,
    config_path: Path,
    config: dict[str, Any],
) -> dict:
    config = {**MODULE_DEFAULTS, **config}
    judge_config = {**JUDGE_DEFAULTS, **config.get("llm_judge", {})}
    judge = (
        LLMJudge(
            mode=str(judge_config["mode"]),
            api_key_env=str(judge_config["api_key_env"]),
        )
        if judge_config["enabled"]
        else None
    )
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

        quality_details = score_text(normalized_text)
        quality_score = quality_details["final_quality_score"]
        if quality_score < config["quality_threshold"]:
            filter_reason_counts["low_quality"] += 1
            continue

        cleaned_record = {
            "text": normalized_text,
            "quality_score": quality_score,
            "quality_details": quality_details,
        }
        if judge:
            cleaned_record["judge_result"] = judge.evaluate(normalized_text)
        cleaned_records.append(cleaned_record)

    cleaned_path = output_dir / "cleaned.jsonl"
    report_path = output_dir / "report.json"
    summary_path = output_dir / "summary.md"
    rag_chunks_path = output_dir / "rag_chunks.jsonl"
    synthetic_qa_path = output_dir / "synthetic_qa.jsonl"
    train_mix_path = output_dir / "train_mix.jsonl"

    downstream_records: list[dict[str, Any]] = []
    for index, record in enumerate(cleaned_records):
        downstream_records.append(
            {
                **record,
                "source_id": f"{input_path.stem}-{index}",
                "metadata": {
                    "source": input_path.stem,
                    "domain": "general",
                    "language": _detect_language(record["text"]),
                },
            }
        )

    rag_chunks = build_chunks(
        downstream_records,
        int(config["rag_chunk_size"]),
        int(config["rag_chunk_overlap"]),
        float(config["rag_chunk_quality_threshold"]),
    )
    synthetic_qa = generate_qa_pairs(
        rag_chunks,
        float(config["synthetic_qa_min_quality"]),
        int(config["synthetic_qa_max_pairs_per_chunk"]),
    )
    train_mix = sample_mixture(
        rag_chunks,
        _mixture_ratios(config),
        int(config["mixture_sample_size"]),
        int(config["mixture_seed"]),
    )

    quality_distributions = {
        metric: _score_summary(
            [record["quality_details"][metric] for record in cleaned_records]
        )
        for metric in QUALITY_METRICS
    }
    scores = [record["quality_score"] for record in cleaned_records]
    judge_results = [
        record["judge_result"] for record in cleaned_records if "judge_result" in record
    ]
    judge_quality_scores = [result["quality_score"] for result in judge_results]
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
            "rag_chunk_size": config["rag_chunk_size"],
            "rag_chunk_overlap": config["rag_chunk_overlap"],
            "rag_chunk_quality_threshold": config["rag_chunk_quality_threshold"],
            "synthetic_qa_min_quality": config["synthetic_qa_min_quality"],
            "llm_judge": judge_config,
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
        "quality_score_summary": _score_summary(scores),
        "quality_distributions": quality_distributions,
        "judge_mode": str(judge_config["mode"]) if judge else "disabled",
        "avg_judge_quality_score": (
            round(sum(judge_quality_scores) / len(judge_quality_scores), 4)
            if judge_quality_scores
            else None
        ),
        "useful_for_pretraining_count": sum(
            result["is_useful_for_pretraining"] for result in judge_results
        ),
        "useful_for_rag_count": sum(
            result["is_useful_for_rag"] for result in judge_results
        ),
        "useful_for_sft_count": sum(
            result["is_useful_for_sft"] for result in judge_results
        ),
        "high_quality_by_judge_count": sum(
            result["quality_score"] >= 4 for result in judge_results
        ),
        "low_quality_by_judge_count": sum(
            result["quality_score"] <= 2
            for result in judge_results
        ),
        "rag_chunk_records": len(rag_chunks),
        "synthetic_qa_records": len(synthetic_qa),
        "train_mix_records": len(train_mix),
        "additional_outputs": {
            "rag_chunks_path": str(rag_chunks_path),
            "synthetic_qa_path": str(synthetic_qa_path),
            "train_mix_path": str(train_mix_path),
        },
    }

    write_jsonl(cleaned_path, cleaned_records)
    write_json(report_path, report)
    write_summary(summary_path, report)
    write_jsonl(rag_chunks_path, rag_chunks)
    write_jsonl(synthetic_qa_path, synthetic_qa)
    write_jsonl(train_mix_path, train_mix)
    return report
