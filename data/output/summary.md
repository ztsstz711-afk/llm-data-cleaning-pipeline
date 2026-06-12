# Data Cleaning Summary

## Run Information

- Run time (UTC): `2026-06-12T15:06:22.041456+00:00`
- Processing time: `0.001` seconds
- Input path: `E:\Projects\llm-data-cleaning-project\data\raw\sample.jsonl`
- Output path: `E:\Projects\llm-data-cleaning-project\data\output\cleaned.jsonl`

## Record Overview

| Metric | Value |
| --- | ---: |
| Total records | 14 |
| Kept records | 4 |
| Removed records | 10 |
| Keep ratio | 0.2857 |
| Duplicate records | 1 |

## Invalid Records

| Reason | Count |
| --- | ---: |
| invalid_json | 1 |
| missing_text | 1 |
| invalid_text_type | 1 |

## Filter Reasons

| Reason | Count |
| --- | ---: |
| empty_text | 1 |
| high_repeated_char_ratio | 1 |
| high_special_char_ratio | 1 |
| low_valid_char_ratio | 1 |
| too_many_urls | 1 |
| too_short | 1 |

## Quality Score Summary

| Statistic | Value |
| --- | ---: |
| Minimum | 0.6466 |
| Maximum | 0.792 |
| Mean | 0.7412 |
| Median | 0.7631 |
