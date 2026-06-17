from pathlib import Path
from typing import Any


REQUIRED_SETTINGS = {
    "min_length",
    "max_length",
    "quality_threshold",
    "max_url_count",
    "max_special_char_ratio",
    "max_repeated_char_ratio",
    "min_valid_char_ratio",
    "rag_chunk_size",
    "rag_chunk_overlap",
    "rag_chunk_quality_threshold",
    "synthetic_qa_min_quality",
    "synthetic_qa_max_pairs_per_chunk",
    "mixture_sample_size",
    "mixture_seed",
    "mixture_source_default",
    "mixture_domain_general",
    "mixture_language_en",
    "mixture_language_zh",
    "mixture_language_unknown",
    "mixture_quality_high",
    "mixture_quality_medium",
    "mixture_quality_low",
}

LLM_JUDGE_SETTINGS = {
    "enabled",
    "mode",
    "quality_threshold",
    "api_key_env",
}


def _parse_scalar(raw_value: str) -> int | float | bool | str:
    lowered = raw_value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return float(raw_value) if "." in raw_value else int(raw_value)
    except ValueError:
        return raw_value


def load_config(path: Path) -> dict[str, Any]:
    """Load the small one-level YAML subset used by this project."""
    config: dict[str, Any] = {}
    current_section: str | None = None

    with path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            without_comment = raw_line.split("#", 1)[0].rstrip()
            line = without_comment.strip()
            if not line:
                continue
            if ":" not in line:
                raise ValueError(f"Invalid config line {line_number}: {raw_line.strip()}")

            key, raw_value = (part.strip() for part in line.split(":", 1))
            is_nested = len(without_comment) > len(without_comment.lstrip())
            if not is_nested and not raw_value:
                if key != "llm_judge":
                    raise ValueError(f"Unknown config section: {key}")
                current_section = key
                config[current_section] = {}
                continue

            if is_nested:
                if current_section != "llm_judge":
                    raise ValueError(f"Unexpected nested config line {line_number}")
                if key not in LLM_JUDGE_SETTINGS:
                    raise ValueError(f"Unknown llm_judge setting: {key}")
                config[current_section][key] = _parse_scalar(raw_value)
                continue

            current_section = None
            if key not in REQUIRED_SETTINGS:
                raise ValueError(f"Unknown config setting: {key}")
            value = _parse_scalar(raw_value)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"Config value for {key} must be a number")
            config[key] = value

    missing_settings = REQUIRED_SETTINGS - config.keys()
    if missing_settings:
        missing = ", ".join(sorted(missing_settings))
        raise ValueError(f"Missing config settings: {missing}")

    judge_config = config.get("llm_judge")
    if not isinstance(judge_config, dict):
        raise ValueError("Missing config section: llm_judge")
    missing_judge_settings = LLM_JUDGE_SETTINGS - judge_config.keys()
    if missing_judge_settings:
        missing = ", ".join(sorted(missing_judge_settings))
        raise ValueError(f"Missing llm_judge settings: {missing}")
    if not isinstance(judge_config["enabled"], bool):
        raise ValueError("llm_judge.enabled must be true or false")
    if judge_config["mode"] not in {"heuristic", "mock", "openai"}:
        raise ValueError("llm_judge.mode must be heuristic, mock, or openai")
    if not 1 <= judge_config["quality_threshold"] <= 5:
        raise ValueError("llm_judge.quality_threshold must be between 1 and 5")
    if not isinstance(judge_config["api_key_env"], str) or not judge_config["api_key_env"]:
        raise ValueError("llm_judge.api_key_env must be a non-empty string")

    if config["min_length"] < 0:
        raise ValueError("min_length must be at least 0")
    if config["max_length"] < config["min_length"]:
        raise ValueError("max_length must be greater than or equal to min_length")
    if not 0 <= config["quality_threshold"] <= 1:
        raise ValueError("quality_threshold must be between 0 and 1")
    if config["max_url_count"] < 0:
        raise ValueError("max_url_count must be at least 0")

    ratio_settings = {
        "max_special_char_ratio",
        "max_repeated_char_ratio",
        "min_valid_char_ratio",
    }
    for setting in ratio_settings:
        if not 0 <= config[setting] <= 1:
            raise ValueError(f"{setting} must be between 0 and 1")

    if config["rag_chunk_size"] <= 0:
        raise ValueError("rag_chunk_size must be greater than 0")
    if not 0 <= config["rag_chunk_overlap"] < config["rag_chunk_size"]:
        raise ValueError("rag_chunk_overlap must be between 0 and rag_chunk_size - 1")
    if not 0 <= config["rag_chunk_quality_threshold"] <= 1:
        raise ValueError("rag_chunk_quality_threshold must be between 0 and 1")
    if not 0 <= config["synthetic_qa_min_quality"] <= 1:
        raise ValueError("synthetic_qa_min_quality must be between 0 and 1")
    if config["synthetic_qa_max_pairs_per_chunk"] < 1:
        raise ValueError("synthetic_qa_max_pairs_per_chunk must be at least 1")
    if config["mixture_sample_size"] < 0:
        raise ValueError("mixture_sample_size must be at least 0")

    mixture_settings = {
        key for key in REQUIRED_SETTINGS if key.startswith("mixture_")
    } - {"mixture_sample_size", "mixture_seed"}
    for setting in mixture_settings:
        if config[setting] < 0:
            raise ValueError(f"{setting} must be at least 0")

    return config
