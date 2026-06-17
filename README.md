# LLM & RAG Data Quality Governance Pipeline

## Quick Overview

This project is a lightweight local pipeline for **LLM training corpus cleaning** and **RAG data governance**.

It reads raw JSONL documents, validates and cleans text, removes exact duplicates, assigns explainable quality scores, runs an optional LLM-as-a-Judge layer, builds RAG chunks, creates template-based synthetic QA examples, samples a training mixture, and writes both machine-readable and human-readable reports.

This is a small, interview-friendly project. It is not a production or distributed data processing system.

## Pipeline Flow

```text
raw JSONL
  -> cleaning/filtering
  -> exact dedup
  -> quality scoring
  -> LLM-as-a-Judge
  -> RAG chunks
  -> synthetic QA
  -> train mix
  -> reports
```

Current deduplication is **SHA-256 exact dedup only**. Near-duplicate detection, MinHash, SimHash, and distributed dedup are not implemented.

## Quick Start

Run the default local demo:

```powershell
python scripts/run_demo.py
```

Run the pipeline directly:

```powershell
python -m src.main
```

Run with explicit paths:

```powershell
python -m src.main --input data/raw/sample.jsonl --output-dir data/output --config configs/default.yaml
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

The default demo uses heuristic LLM-as-a-Judge mode and does not call any external API.

## Demo Results

Current demo metrics from `python scripts/run_demo.py`:

```text
Cleaned records: 11
RAG chunks: 11
Synthetic QA pairs: 11
Training mixture records: 11
High quality by judge: 8
Low quality by judge: 3
Useful for RAG: 8
Useful for SFT: 8
Average judge score: 3.4545
Tests: 34 OK
```

These numbers are based on the small sample dataset in `data/raw/sample.jsonl`.

## Input Format

Input data is JSONL. Each line should be a JSON object with a string `text` field:

```json
{"text": "Large language models require clean and diverse training data."}
```

The sample dataset includes high-quality technical text, low-quality noisy text, marketing text, URL boilerplate, exact duplicates, near-duplicate examples, fictional PII-like text, RAG-style knowledge text, and educational QA-style text.

## Outputs

The demo writes outputs to `data/output/`:

| File | Purpose |
| --- | --- |
| `cleaned.jsonl` | Cleaned documents with quality scores and judge results |
| `rag_chunks.jsonl` | Fixed-length RAG chunks with source metadata |
| `synthetic_qa.jsonl` | Template-based QA examples generated from chunks |
| `train_mix.jsonl` | Sampled training mixture records |
| `report.json` | Machine-readable metrics and quality distributions |
| `summary.md` | Human-readable Markdown summary |

Example cleaned record:

```json
{
  "text": "Large language models require clean and diverse training data.",
  "quality_score": 0.712,
  "quality_details": {
    "length_score": 0.3233,
    "readability_score": 0.7371,
    "informativeness_score": 0.5133,
    "noise_score": 1.0,
    "repetition_score": 0.9607,
    "final_quality_score": 0.712
  },
  "judge_result": {
    "quality_score": 4,
    "educational_value": 4,
    "informativeness": 3,
    "noise_level": 1,
    "is_spam": false,
    "is_useful_for_pretraining": true,
    "is_useful_for_rag": true,
    "is_useful_for_sft": true,
    "reason": "Heuristic score 4/5..."
  }
}
```

## Key Modules

| Module | Role |
| --- | --- |
| `src/main.py` | CLI entry point |
| `src/pipeline.py` | End-to-end orchestration |
| `src/jsonl_io.py` | JSONL reading, validation, and writing |
| `src/cleaning.py` | Normalization, rule filtering, and SHA-256 hashing |
| `src/quality_scorer.py` | Multi-dimensional heuristic quality scoring |
| `src/llm_judge.py` | LLM-as-a-Judge interface with heuristic, mock, and openai modes |
| `src/prompt_templates.py` | Prompt and JSON schema for judge mode |
| `src/rag_chunker.py` | Fixed-length RAG chunk builder with overlap |
| `src/synthetic_qa.py` | Template-based QA generation demo |
| `src/data_mixer.py` | Source/domain/language/quality-level mixture sampler |
| `src/summary.py` | Markdown summary writer |
| `src/config.py` | Minimal YAML-like config loader |

## LLM-as-a-Judge Modes

The project supports three judge modes:

- `heuristic`: default local mode; no API call, deterministic behavior.
- `mock`: fixed structured result for tests.
- `openai`: optional OpenAI-compatible Chat Completions API mode.

The default config keeps:

```yaml
llm_judge:
  enabled: true
  mode: heuristic
  quality_threshold: 3
  api_key_env: OPENAI_API_KEY
```

To try the real API demo, install the optional dependency and set environment variables:

```powershell
python -m pip install -r requirements.txt
$env:OPENAI_API_KEY="your-api-key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_MODEL="your-chat-completions-model"
python scripts/run_llm_judge_api_demo.py
```

The main demo does not depend on API keys.

## Configuration

Main config file:

```text
configs/default.yaml
```

It controls:

- text length thresholds
- URL and special-character filters
- quality threshold
- RAG chunk size and overlap
- synthetic QA quality threshold
- mixture sampling ratios
- LLM judge mode

The config loader intentionally supports only the small YAML subset used by this project.

## Tests

The project uses Python standard-library `unittest`.

Current coverage includes:

- text normalization and filtering
- JSONL validation
- exact hash behavior
- quality scoring
- LLM-as-a-Judge heuristic/mock/openai contract behavior
- RAG chunking
- synthetic QA generation
- data mixture sampling
- end-to-end pipeline outputs

Run:

```powershell
python -m unittest discover -s tests -v
```

Current expected result:

```text
Ran 34 tests
OK
```

## Limitations

- No near-duplicate detection yet.
- No MinHash, SimHash, or LSH.
- No distributed processing.
- No GPU acceleration.
- No vector database integration.
- No model perplexity scoring.
- Real LLM judging is optional and not used by the default demo.
- The sample dataset is intentionally small and designed for demonstration.

## Resume-Friendly Summary

Built a lightweight Python data quality governance pipeline for LLM training corpus and RAG data preparation, including JSONL validation, rule-based filtering, SHA-256 exact deduplication, multi-dimensional heuristic quality scoring, LLM-as-a-Judge compatible evaluation, RAG chunking, template-based synthetic QA generation, data mixture sampling, and JSON/Markdown reporting with unittest coverage.
