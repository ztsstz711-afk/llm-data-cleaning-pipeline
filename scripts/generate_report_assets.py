import argparse
import csv
import json
from html import escape
from pathlib import Path
from typing import Any


DEFAULT_REPORT_PATH = Path("data/output/report.json")
DEFAULT_OUTPUT_DIR = Path("data/output/report_assets")


def _write_filter_reasons_csv(path: Path, filter_counts: dict[str, int]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["reason", "count"])
        for reason, count in sorted(filter_counts.items()):
            writer.writerow([reason, count])


def _write_quality_summary_csv(path: Path, quality_summary: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])
        for metric, value in quality_summary.items():
            writer.writerow([metric, value])


def _bar_svg(title: str, items: list[tuple[str, int]], empty_message: str) -> str:
    width = 720
    row_height = 34
    top_padding = 54
    left_padding = 190
    chart_width = 420
    height = max(140, top_padding + row_height * max(len(items), 1) + 24)
    max_value = max((value for _, value in items), default=0)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700">{escape(title)}</text>',
    ]
    if not items:
        lines.append(
            f'<text x="24" y="{top_padding + 24}" font-family="Arial, sans-serif" font-size="15" fill="#555">{escape(empty_message)}</text>'
        )
    else:
        for index, (label, value) in enumerate(items):
            y = top_padding + index * row_height
            bar_width = 0 if max_value == 0 else int(chart_width * value / max_value)
            lines.extend(
                [
                    f'<text x="24" y="{y + 18}" font-family="Arial, sans-serif" font-size="13">{escape(label)}</text>',
                    f'<rect x="{left_padding}" y="{y}" width="{bar_width}" height="20" fill="#4f81bd"/>',
                    f'<text x="{left_padding + bar_width + 8}" y="{y + 15}" font-family="Arial, sans-serif" font-size="13">{value}</text>',
                ]
            )
    lines.append("</svg>")
    return "\n".join(lines)


def _write_record_overview_svg(path: Path, report: dict[str, Any]) -> None:
    items = [
        ("total_records", int(report.get("total_records", 0))),
        ("kept_records", int(report.get("kept_records", 0))),
        ("removed_records", int(report.get("removed_records", 0))),
        ("duplicate_records", int(report.get("duplicate_records", 0))),
        ("near_duplicate_records", int(report.get("near_duplicate_records", 0))),
    ]
    path.write_text(
        _bar_svg("Record Overview", items, "No record metrics"),
        encoding="utf-8",
    )


def _write_filter_reasons_svg(path: Path, filter_counts: dict[str, int]) -> None:
    path.write_text(
        _bar_svg(
            "Filter Reasons",
            sorted((reason, int(count)) for reason, count in filter_counts.items()),
            "No filter reasons",
        ),
        encoding="utf-8",
    )


def generate_report_assets(
    report_path: Path = DEFAULT_REPORT_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> None:
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    filter_counts = report.get("filter_reason_counts", {})
    quality_summary = report.get("quality_score_summary", {})

    _write_filter_reasons_csv(output_dir / "filter_reasons.csv", filter_counts)
    _write_quality_summary_csv(output_dir / "quality_summary.csv", quality_summary)
    _write_record_overview_svg(output_dir / "record_overview.svg", report)
    _write_filter_reasons_svg(output_dir / "filter_reasons.svg", filter_counts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate static report assets.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        generate_report_assets(args.report, args.output_dir)
    except FileNotFoundError as error:
        raise SystemExit(str(error)) from error
    print(f"Report assets written to: {args.output_dir}")


if __name__ == "__main__":
    main()

