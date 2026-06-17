import json
import tempfile
import unittest
from pathlib import Path

from src.pipeline import run_pipeline


TEST_CONFIG = {
    "min_length": 20,
    "max_length": 5000,
    "quality_threshold": 0.0,
    "max_url_count": 2,
    "max_special_char_ratio": 0.3,
    "max_repeated_char_ratio": 0.5,
    "min_valid_char_ratio": 0.5,
}


class PipelineTests(unittest.TestCase):
    def test_pipeline_creates_outputs_and_consistent_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "sample.jsonl"
            output_dir = temp_path / "output"
            config_path = temp_path / "config.yaml"

            records = [
                {"text": "A useful document with enough text to pass filtering."},
                {"text": "A useful document with enough text to pass filtering."},
                {"text": "Short text."},
            ]
            input_path.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )

            report = run_pipeline(input_path, output_dir, config_path, TEST_CONFIG)

            self.assertTrue((output_dir / "cleaned.jsonl").exists())
            self.assertTrue((output_dir / "report.json").exists())
            self.assertTrue((output_dir / "rag_chunks.jsonl").exists())
            self.assertTrue((output_dir / "synthetic_qa.jsonl").exists())
            self.assertTrue((output_dir / "train_mix.jsonl").exists())
            self.assertEqual(report["total_records"], 3)
            self.assertEqual(report["kept_records"], 1)
            self.assertEqual(report["removed_records"], 2)
            self.assertEqual(report["judge_mode"], "heuristic")
            cleaned_record = json.loads(
                (output_dir / "cleaned.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()[0]
            )
            self.assertIn("judge_result", cleaned_record)
            self.assertEqual(
                report["total_records"],
                report["kept_records"] + report["removed_records"],
            )

    def test_pipeline_creates_markdown_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "sample.jsonl"
            output_dir = temp_path / "output"
            config_path = temp_path / "config.yaml"
            input_path.write_text(
                json.dumps(
                    {"text": "A useful document with enough text for the summary."}
                )
                + "\n",
                encoding="utf-8",
            )

            run_pipeline(input_path, output_dir, config_path, TEST_CONFIG)

            summary_path = output_dir / "summary.md"
            self.assertTrue(summary_path.exists())
            summary = summary_path.read_text(encoding="utf-8")
            self.assertIn("# Data Cleaning Summary", summary)
            self.assertIn("Total records", summary)
            self.assertIn("Quality Score Summary", summary)

    def test_pipeline_can_filter_near_duplicates_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "sample.jsonl"
            output_dir = temp_path / "output"
            config_path = temp_path / "config.yaml"
            config = {
                **TEST_CONFIG,
                "near_dedup_enabled": True,
                "simhash_threshold": 8,
                "simhash_num_bits": 64,
            }
            records = [
                {
                    "text": (
                        "Large language models require clean and diverse training data "
                        "for reliable model behavior."
                    )
                },
                {
                    "text": (
                        "Large language models require clean, diverse training data "
                        "for reliable model behavior."
                    )
                },
            ]
            input_path.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )

            report = run_pipeline(input_path, output_dir, config_path, config)

            self.assertEqual(report["near_duplicate_records"], 1)
            self.assertEqual(report["filter_reason_counts"]["near_duplicate"], 1)


if __name__ == "__main__":
    unittest.main()
