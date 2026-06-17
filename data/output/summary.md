# Data Cleaning Summary

## Run Information

- Run time (UTC): `2026-06-17T07:15:34.077551+00:00`
- Processing time: `0.0039` seconds
- Input path: `E:\Projects\llm-data-cleaning-project\data\raw\sample.jsonl`
- Output path: `E:\Projects\llm-data-cleaning-project\data\output\cleaned.jsonl`

## Record Overview

| Metric | Value |
| --- | ---: |
| Total records | 21 |
| Kept records | 11 |
| Removed records | 10 |
| Keep ratio | 0.5238 |
| Duplicate records | 1 |
| Near duplicate records | 0 |

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
| Minimum | 0.712 |
| Maximum | 0.8754 |
| Mean | 0.7836 |
| Median | 0.7625 |

## LLM-as-a-Judge Summary

| Metric | Value |
| --- | ---: |
| Judge mode | heuristic |
| Average judge quality | 3.4545 |
| High-quality records | 8 |
| Low-quality records | 3 |
| Useful for RAG | 8 |
| Useful for SFT | 8 |
