import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.pipeline import run_pipeline


def main() -> None:
    input_path = PROJECT_ROOT / "data" / "raw" / "sample.jsonl"
    output_dir = PROJECT_ROOT / "data" / "output"
    config_path = PROJECT_ROOT / "configs" / "default.yaml"
    report = run_pipeline(input_path, output_dir, config_path, load_config(config_path))

    print("Full LLM and RAG data quality demo completed.")
    print(f"Cleaned records: {report['kept_records']}")
    print(f"RAG chunks: {report['rag_chunk_records']}")
    print(f"Synthetic QA pairs: {report['synthetic_qa_records']}")
    print(f"Training mixture records: {report['train_mix_records']}")
    print(f"High quality by judge: {report['high_quality_by_judge_count']}")
    print(f"Low quality by judge: {report['low_quality_by_judge_count']}")
    print(f"Useful for RAG: {report['useful_for_rag_count']}")
    print(f"Useful for SFT: {report['useful_for_sft_count']}")
    print(f"Average judge score: {report['avg_judge_quality_score']}")
    print(f"Outputs: {output_dir}")


if __name__ == "__main__":
    main()
