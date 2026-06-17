import os
import sys
import types
import unittest
from unittest.mock import patch

from src.llm_judge import LLMJudge, MOCK_RESULT


class LLMJudgeTests(unittest.TestCase):
    def test_heuristic_mode_returns_structured_result(self) -> None:
        result = LLMJudge(mode="heuristic").evaluate(
            "Data quality rules improve model training and retrieval reliability."
        )
        expected_fields = {
            "quality_score",
            "educational_value",
            "informativeness",
            "noise_level",
            "is_spam",
            "is_useful_for_pretraining",
            "is_useful_for_rag",
            "is_useful_for_sft",
            "reason",
        }
        self.assertEqual(set(result), expected_fields)
        self.assertTrue(1 <= result["quality_score"] <= 5)

    def test_mock_mode_returns_fixed_result(self) -> None:
        result = LLMJudge(mode="mock").evaluate("Any test input")
        self.assertEqual(result, MOCK_RESULT)

    def test_low_quality_text_receives_low_score(self) -> None:
        result = LLMJudge(mode="heuristic").evaluate("@" * 50)
        self.assertLessEqual(result["quality_score"], 2)
        self.assertFalse(result["is_useful_for_pretraining"])
        self.assertFalse(result["is_useful_for_rag"])

    def test_advertising_text_is_low_quality_or_spam(self) -> None:
        text = (
            "LIMITED OFFER: buy now for a huge discount. Click here for a free "
            "trial and subscribe at https://promo.example/deal before the sale ends."
        )
        result = LLMJudge(mode="heuristic").evaluate(text)
        self.assertTrue(result["is_spam"] or result["quality_score"] <= 2)
        self.assertFalse(result["is_useful_for_rag"])

    def test_garbled_text_receives_low_score(self) -> None:
        text = (
            "Decoded payload contains invalid bytes ���������� and broken fragments, "
            "so the original document cannot be trusted."
        )
        result = LLMJudge(mode="heuristic").evaluate(text)
        self.assertLessEqual(result["quality_score"], 2)

    def test_url_boilerplate_receives_low_score(self) -> None:
        text = (
            "Mirror pages https://noise.example/a and https://noise.example/b "
            "repeat navigation, cookie notice, login prompt, and footer text."
        )
        result = LLMJudge(mode="heuristic").evaluate(text)
        self.assertLessEqual(result["quality_score"], 2)
        self.assertFalse(result["is_useful_for_rag"])

    def test_short_text_receives_low_score(self) -> None:
        result = LLMJudge(mode="heuristic").evaluate("Tiny note.")
        self.assertLessEqual(result["quality_score"], 2)

    def test_high_quality_technical_text_receives_high_score(self) -> None:
        text = (
            "Python uses reference counting and a cyclic garbage collector. "
            "The collector identifies unreachable object cycles, while reference "
            "counts release most objects deterministically. This behavior helps "
            "developers reason about memory management in long-running pipelines."
        )
        result = LLMJudge(mode="heuristic").evaluate(text)
        self.assertGreaterEqual(result["quality_score"], 4)
        self.assertTrue(result["is_useful_for_pretraining"])
        self.assertTrue(result["is_useful_for_rag"])
        self.assertTrue(result["is_useful_for_sft"])

    def test_educational_qa_text_is_useful_for_sft(self) -> None:
        text = (
            "Question: Why is validation data separated from training data? "
            "Answer: It measures generalization on unseen examples and supports "
            "model selection without fitting directly to the test set."
        )
        result = LLMJudge(mode="heuristic").evaluate(text)
        self.assertTrue(result["is_useful_for_sft"])
        self.assertTrue(result["is_useful_for_rag"])

    def test_openai_mode_requires_api_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                LLMJudge(mode="openai").evaluate("A document")

    def test_openai_mode_calls_chat_completions_and_parses_json(self) -> None:
        expected_result = {
            "quality_score": 5,
            "educational_value": 5,
            "informativeness": 5,
            "noise_level": 1,
            "is_spam": False,
            "is_useful_for_pretraining": True,
            "is_useful_for_rag": True,
            "is_useful_for_sft": True,
            "reason": "Clear technical explanation.",
        }
        captured: dict = {}

        class FakeResponse:
            text = ""

            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict:
                return {
                    "choices": [
                        {"message": {"content": __import__("json").dumps(expected_result)}}
                    ]
                }

        def fake_post(url: str, **kwargs) -> FakeResponse:
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse()

        fake_requests = types.SimpleNamespace(
            post=fake_post,
            RequestException=Exception,
        )
        environment = {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_BASE_URL": "https://compatible.example/v1",
            "OPENAI_MODEL": "test-model",
        }
        with patch.dict(os.environ, environment, clear=True), patch.dict(
            sys.modules, {"requests": fake_requests}
        ):
            result = LLMJudge(mode="openai").evaluate("Technical document")

        self.assertEqual(result, expected_result)
        self.assertEqual(captured["url"], "https://compatible.example/v1/chat/completions")
        self.assertEqual(captured["json"]["model"], "test-model")
        self.assertEqual(captured["json"]["response_format"], {"type": "json_object"})
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-key")


if __name__ == "__main__":
    unittest.main()
