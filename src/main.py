import argparse
from pathlib import Path

from src.config import load_config
from src.pipeline import run_pipeline


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = Path("data/raw/sample.jsonl")
DEFAULT_OUTPUT_DIR = Path("data/output")
DEFAULT_CONFIG_PATH = Path("configs/default.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean JSONL text data for LLM pre-training."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="Input JSONL file (default: data/raw/sample.jsonl)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory (default: data/output)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Configuration file (default: configs/default.yaml)",
    )
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def main() -> None:
    args = parse_args()
    input_path = resolve_path(args.input)
    output_dir = resolve_path(args.output_dir)
    config_path = resolve_path(args.config)
    config = load_config(config_path)

    report = run_pipeline(input_path, output_dir, config_path, config)
    print("Cleaning completed.")
    print(f"Kept records: {report['kept_records']}")
    print(f"Cleaned data: {output_dir / 'cleaned.jsonl'}")
    print(f"Report: {output_dir / 'report.json'}")


if __name__ == "__main__":
    main()
