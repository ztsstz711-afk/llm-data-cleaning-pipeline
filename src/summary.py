from pathlib import Path
from typing import Any


def _format_value(value: Any) -> str:
    return "N/A" if value is None else str(value)


def write_summary(path: Path, report: dict[str, Any]) -> None:
    """Write a human-readable Markdown summary from the JSON report data."""
    invalid_counts = report["invalid_record_counts"]
    filter_counts = sorted(
        report["filter_reason_counts"].items(),
        key=lambda item: (-item[1], item[0]),
    )
    quality = report["quality_score_summary"]

    lines = [
        "# Data Cleaning Summary",
        "",
        "## Run Information",
        "",
        f"- Run time (UTC): `{report['started_at_utc']}`",
        f"- Processing time: `{report['processing_time_seconds']}` seconds",
        f"- Input path: `{report['input_path']}`",
        f"- Output path: `{report['output_path']}`",
        "",
        "## Record Overview",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Total records | {report['total_records']} |",
        f"| Kept records | {report['kept_records']} |",
        f"| Removed records | {report['removed_records']} |",
        f"| Keep ratio | {report['keep_ratio']:.4f} |",
        f"| Duplicate records | {report['duplicate_records']} |",
        "",
        "## Invalid Records",
        "",
        "| Reason | Count |",
        "| --- | ---: |",
    ]

    lines.extend(
        f"| {reason} | {count} |" for reason, count in invalid_counts.items()
    )
    lines.extend(
        [
            "",
            "## Filter Reasons",
            "",
            "| Reason | Count |",
            "| --- | ---: |",
        ]
    )
    if filter_counts:
        lines.extend(f"| {reason} | {count} |" for reason, count in filter_counts)
    else:
        lines.append("| No filtered records | 0 |")

    lines.extend(
        [
            "",
            "## Quality Score Summary",
            "",
            "| Statistic | Value |",
            "| --- | ---: |",
            f"| Minimum | {_format_value(quality['min'])} |",
            f"| Maximum | {_format_value(quality['max'])} |",
            f"| Mean | {_format_value(quality['mean'])} |",
            f"| Median | {_format_value(quality['median'])} |",
            "",
        ]
    )

    if "judge_mode" in report:
        lines.extend(
            [
                "## LLM-as-a-Judge Summary",
                "",
                "| Metric | Value |",
                "| --- | ---: |",
                f"| Judge mode | {report['judge_mode']} |",
                f"| Average judge quality | {_format_value(report['avg_judge_quality_score'])} |",
                f"| High-quality records | {report['high_quality_by_judge_count']} |",
                f"| Low-quality records | {report['low_quality_by_judge_count']} |",
                f"| Useful for RAG | {report['useful_for_rag_count']} |",
                f"| Useful for SFT | {report['useful_for_sft_count']} |",
                "",
            ]
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
