import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_report_assets import generate_report_assets


class ReportAssetsTests(unittest.TestCase):
    def test_generate_report_assets_creates_csv_and_svg_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "report.json"
            output_dir = temp_path / "assets"
            report = {
                "total_records": 10,
                "kept_records": 6,
                "removed_records": 4,
                "duplicate_records": 1,
                "near_duplicate_records": 2,
                "filter_reason_counts": {
                    "too_short": 1,
                    "near_duplicate": 2,
                },
                "quality_score_summary": {
                    "min": 0.1,
                    "max": 0.9,
                    "mean": 0.5,
                    "median": 0.6,
                },
            }
            report_path.write_text(json.dumps(report), encoding="utf-8")

            generate_report_assets(report_path, output_dir)

            expected_files = [
                "filter_reasons.csv",
                "quality_summary.csv",
                "record_overview.svg",
                "filter_reasons.svg",
            ]
            for filename in expected_files:
                self.assertTrue((output_dir / filename).exists(), filename)

            filter_csv = (output_dir / "filter_reasons.csv").read_text(encoding="utf-8")
            quality_csv = (output_dir / "quality_summary.csv").read_text(encoding="utf-8")
            record_svg = (output_dir / "record_overview.svg").read_text(encoding="utf-8")
            filter_svg = (output_dir / "filter_reasons.svg").read_text(encoding="utf-8")

            self.assertIn("reason,count", filter_csv)
            self.assertIn("near_duplicate,2", filter_csv)
            self.assertIn("metric,value", quality_csv)
            self.assertIn("mean,0.5", quality_csv)
            self.assertIn("<svg", record_svg)
            self.assertIn("near_duplicate_records", record_svg)
            self.assertIn("<svg", filter_svg)

    def test_empty_filter_reasons_still_creates_valid_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "report.json"
            output_dir = temp_path / "assets"
            report_path.write_text(
                json.dumps(
                    {
                        "total_records": 1,
                        "kept_records": 1,
                        "removed_records": 0,
                        "duplicate_records": 0,
                        "near_duplicate_records": 0,
                        "filter_reason_counts": {},
                        "quality_score_summary": {},
                    }
                ),
                encoding="utf-8",
            )

            generate_report_assets(report_path, output_dir)

            filter_svg = (output_dir / "filter_reasons.svg").read_text(encoding="utf-8")
            self.assertIn("<svg", filter_svg)
            self.assertIn("No filter reasons", filter_svg)


if __name__ == "__main__":
    unittest.main()

