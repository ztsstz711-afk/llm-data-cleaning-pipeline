import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.llm_judge import LLMJudge


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "OPENAI_API_KEY is not set. Set it before running the real LLM judge "
            "API demo. The main demo continues to use heuristic mode."
        )
        return

    input_path = PROJECT_ROOT / "data" / "raw" / "sample.jsonl"
    judge = LLMJudge(mode="openai")
    evaluated = 0

    with input_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if evaluated >= 2:
                break
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = record.get("text") if isinstance(record, dict) else None
            if not isinstance(text, str) or not text.strip():
                continue

            result = judge.evaluate(text)
            print(json.dumps({"line": line_number, "judge_result": result}, ensure_ascii=False))
            evaluated += 1


if __name__ == "__main__":
    main()
