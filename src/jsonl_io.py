import json
from pathlib import Path
from typing import Any, Iterator


def read_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any] | None, str | None]]:
    """Yield line number, parsed object, and an optional validation error."""
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                yield line_number, None, "invalid_json"
                continue

            if not isinstance(record, dict):
                yield line_number, None, "not_an_object"
            elif "text" not in record:
                yield line_number, None, "missing_text"
            elif not isinstance(record["text"], str):
                yield line_number, None, "text_not_string"
            else:
                yield line_number, record, None


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")

