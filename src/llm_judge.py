import json
import os
import re
from typing import Any

from src.prompt_templates import (
    JUDGE_JSON_SCHEMA,
    LLM_JUDGE_SYSTEM_PROMPT,
    build_judge_prompt,
)
from src.quality_scorer import score_text


MOCK_RESULT = {
    "quality_score": 4,
    "educational_value": 4,
    "informativeness": 4,
    "noise_level": 1,
    "is_spam": False,
    "is_useful_for_pretraining": True,
    "is_useful_for_rag": True,
    "is_useful_for_sft": True,
    "reason": "Fixed mock evaluation for deterministic tests.",
}


class LLMJudge:
    """Evaluate text with heuristic, mock, or OpenAI structured-output modes."""

    MODES = {"heuristic", "mock", "openai"}

    def __init__(
        self,
        mode: str = "heuristic",
        api_key_env: str = "OPENAI_API_KEY",
        model: str | None = None,
    ) -> None:
        if mode not in self.MODES:
            raise ValueError(f"Unsupported LLM judge mode: {mode}")
        self.mode = mode
        self.api_key_env = api_key_env
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    def evaluate(self, text: str) -> dict[str, Any]:
        if self.mode == "mock":
            return dict(MOCK_RESULT)
        if self.mode == "openai":
            return self._evaluate_openai(text)
        return self._evaluate_heuristic(text)

    def _evaluate_heuristic(self, text: str) -> dict[str, Any]:
        scores = score_text(text)
        lowered = text.lower()
        url_count = len(re.findall(r"https?://\S+|www\.\S+", text, re.IGNORECASE))
        spam_terms = re.findall(
            r"\b(?:buy now|limited offer|discount|free trial|click here|subscribe|winner|sale)\b",
            lowered,
        )
        boilerplate_terms = re.findall(
            r"\b(?:cookie notice|navigation|login prompt|footer text|sign in|privacy policy)\b",
            lowered,
        )
        contact_count = len(
            re.findall(
                r"[\w.+-]+@[\w.-]+\.\w+|\+?\d[\d\s()-]{7,}\d",
                text,
            )
        )
        decode_error_count = text.count("\ufffd") + len(
            re.findall(r"(?:Ã.|Â.|â.|ï¿½)", text)
        )
        too_short_for_knowledge = len(text.strip()) < 45
        final_score = scores["final_quality_score"]
        penalty = 0
        if scores["noise_score"] < 0.8:
            penalty += 1
        if decode_error_count >= 3:
            penalty += 2
        if url_count >= 2:
            penalty += 2
        elif url_count == 1 and scores["informativeness_score"] < 0.5:
            penalty += 1
        if len(boilerplate_terms) >= 2:
            penalty += 1
        if spam_terms:
            penalty += min(2, len(spam_terms))
        if too_short_for_knowledge:
            penalty += 1
        quality_score = max(1, self._to_five_point(final_score) - penalty)
        educational_value = self._to_five_point(
            0.45 * scores["readability_score"]
            + 0.55 * scores["informativeness_score"]
        )
        informativeness = self._to_five_point(scores["informativeness_score"])
        noise_level = 6 - self._to_five_point(scores["noise_score"])
        is_spam = bool(spam_terms) or noise_level >= 4 or (
            scores["repetition_score"] < 0.45
            and scores["informativeness_score"] < 0.35
        )
        useful_for_pretraining = quality_score >= 3 and not is_spam
        useful_for_rag = (
            quality_score >= 3
            and informativeness >= 3
            and noise_level <= 3
            and not is_spam
        )
        useful_for_sft = (
            quality_score >= 3
            and educational_value >= 3
            and informativeness >= 3
            and noise_level <= 3
            and not is_spam
        )

        reason = (
            f"Heuristic score {quality_score}/5: informativeness "
            f"{informativeness}/5, noise {noise_level}/5, and repetition quality "
            f"{scores['repetition_score']:.2f}; detected {url_count} URL(s), "
            f"{len(spam_terms)} marketing phrase(s), {len(boilerplate_terms)} "
            f"boilerplate phrase(s), {contact_count} contact item(s), and "
            f"{decode_error_count} decode error marker(s)."
        )
        return {
            "quality_score": quality_score,
            "educational_value": educational_value,
            "informativeness": informativeness,
            "noise_level": noise_level,
            "is_spam": is_spam,
            "is_useful_for_pretraining": useful_for_pretraining,
            "is_useful_for_rag": useful_for_rag,
            "is_useful_for_sft": useful_for_sft,
            "reason": reason,
        }

    def _evaluate_openai(self, text: str) -> dict[str, Any]:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"LLM judge mode 'openai' requires the {self.api_key_env} "
                "environment variable. Set it or use heuristic/mock mode."
            )

        try:
            import requests
        except ImportError as error:
            raise RuntimeError(
                "LLM judge mode 'openai' requires the requests package. "
                "Install it with: python -m pip install requests"
            ) from error

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": LLM_JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": build_judge_prompt(text)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                },
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            detail = getattr(error.response, "text", "") if error.response else ""
            suffix = f": {detail}" if detail else ""
            raise RuntimeError(f"OpenAI-compatible judge request failed{suffix}") from error

        try:
            response_data = response.json()
            output_text = response_data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise RuntimeError(
                "OpenAI-compatible judge response did not contain "
                "choices[0].message.content"
            ) from error

        try:
            result = json.loads(output_text)
        except (json.JSONDecodeError, TypeError) as error:
            raise RuntimeError(
                "OpenAI-compatible judge returned invalid JSON content"
            ) from error
        self._validate_result(result)
        return result

    @staticmethod
    def _to_five_point(score: float) -> int:
        return max(1, min(5, round(score * 4) + 1))

    @staticmethod
    def _validate_result(result: dict[str, Any]) -> None:
        required = JUDGE_JSON_SCHEMA["required"]
        missing = [field for field in required if field not in result]
        if missing:
            raise ValueError(f"LLM judge result is missing fields: {', '.join(missing)}")
        for field in ("quality_score", "educational_value", "informativeness", "noise_level"):
            if not isinstance(result[field], int) or not 1 <= result[field] <= 5:
                raise ValueError(f"LLM judge field {field} must be an integer from 1 to 5")
