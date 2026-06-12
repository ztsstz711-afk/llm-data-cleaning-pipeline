from pathlib import Path


REQUIRED_SETTINGS = {
    "min_length",
    "max_length",
    "quality_threshold",
    "max_url_count",
    "max_special_char_ratio",
    "max_repeated_char_ratio",
    "min_valid_char_ratio",
}


def load_config(path: Path) -> dict[str, int | float]:
    """Load the simple key-value YAML format used by this project."""
    config: dict[str, int | float] = {}

    with path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if ":" not in line:
                raise ValueError(f"Invalid config line {line_number}: {raw_line.strip()}")

            key, raw_value = (part.strip() for part in line.split(":", 1))
            if key not in REQUIRED_SETTINGS:
                raise ValueError(f"Unknown config setting: {key}")

            try:
                config[key] = float(raw_value) if "." in raw_value else int(raw_value)
            except ValueError as error:
                raise ValueError(f"Config value for {key} must be a number") from error

    missing_settings = REQUIRED_SETTINGS - config.keys()
    if missing_settings:
        missing = ", ".join(sorted(missing_settings))
        raise ValueError(f"Missing config settings: {missing}")

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

    return config
