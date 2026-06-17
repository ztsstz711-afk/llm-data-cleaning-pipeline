import json


LLM_JUDGE_SYSTEM_PROMPT = """You are a strict data quality evaluator.
Evaluate whether the supplied text is useful for LLM pretraining, a RAG knowledge
base, and SFT or synthetic QA generation. Consider factual density, educational
value, readability, repetition, spam, and noise.

Return only valid JSON matching the requested schema. Do not add Markdown,
explanations outside the JSON object, or additional keys.
"""


def build_judge_prompt(text: str) -> str:
    criteria = {
        "quality_score": "Integer 1-5; overall data quality",
        "educational_value": "Integer 1-5; learning value",
        "informativeness": "Integer 1-5; useful factual content",
        "noise_level": "Integer 1-5; 1 is clean and 5 is very noisy",
        "is_spam": "Boolean",
        "is_useful_for_pretraining": "Boolean",
        "is_useful_for_rag": "Boolean",
        "is_useful_for_sft": "Boolean; suitable for instruction or QA generation",
        "reason": "Short explanation",
    }
    return (
        "Evaluate the text for LLM pretraining, RAG knowledge base use, and "
        "SFT or synthetic QA generation.\n\n"
        f"Required fields:\n{json.dumps(criteria, ensure_ascii=False, indent=2)}\n\n"
        f"Text:\n{text}"
    )


JUDGE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "quality_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "educational_value": {"type": "integer", "minimum": 1, "maximum": 5},
        "informativeness": {"type": "integer", "minimum": 1, "maximum": 5},
        "noise_level": {"type": "integer", "minimum": 1, "maximum": 5},
        "is_spam": {"type": "boolean"},
        "is_useful_for_pretraining": {"type": "boolean"},
        "is_useful_for_rag": {"type": "boolean"},
        "is_useful_for_sft": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": [
        "quality_score",
        "educational_value",
        "informativeness",
        "noise_level",
        "is_spam",
        "is_useful_for_pretraining",
        "is_useful_for_rag",
        "is_useful_for_sft",
        "reason",
    ],
    "additionalProperties": False,
}
