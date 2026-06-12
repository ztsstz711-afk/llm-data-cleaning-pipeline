import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from src.jsonl_io import read_jsonl


class JsonlIoTests(unittest.TestCase):
    def read_lines(self, lines: list[str]) -> list[tuple]:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.jsonl"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return list(read_jsonl(path))

    def test_valid_jsonl_can_be_read(self) -> None:
        results = self.read_lines([json.dumps({"text": "A valid document."})])
        self.assertEqual(results[0][1], {"text": "A valid document."})
        self.assertIsNone(results[0][2])

    def test_invalid_json_is_counted(self) -> None:
        results = self.read_lines(["not valid json"])
        counts = Counter(result[2] for result in results if result[2])
        self.assertEqual(counts["invalid_json"], 1)

    def test_missing_text_is_counted(self) -> None:
        results = self.read_lines([json.dumps({"content": "No text field"})])
        counts = Counter(result[2] for result in results if result[2])
        self.assertEqual(counts["missing_text"], 1)

    def test_invalid_text_type_is_counted(self) -> None:
        results = self.read_lines([json.dumps({"text": 123})])
        counts = Counter(
            "invalid_text_type" if result[2] == "text_not_string" else result[2]
            for result in results
            if result[2]
        )
        self.assertEqual(counts["invalid_text_type"], 1)


if __name__ == "__main__":
    unittest.main()

