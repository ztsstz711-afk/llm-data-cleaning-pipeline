import unittest

from src.synthetic_qa import generate_qa_pairs


class SyntheticQaTests(unittest.TestCase):
    def test_generates_template_qa_from_high_quality_chunk(self) -> None:
        chunks = [
            {
                "source_id": "doc-1",
                "chunk_id": "doc-1-chunk-0",
                "text": "Data quality improves retrieval results. A second sentence follows.",
                "quality_score": 0.9,
                "metadata": {"domain": "rag"},
            }
        ]
        pairs = generate_qa_pairs(chunks, min_quality=0.8)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["chunk_id"], "doc-1-chunk-0")
        self.assertIn("question", pairs[0])
        self.assertIn("answer", pairs[0])
        self.assertEqual(pairs[0]["metadata"]["generator"], "template_demo")

    def test_skips_low_quality_chunk(self) -> None:
        chunks = [
            {
                "source_id": "doc-1",
                "chunk_id": "chunk-0",
                "text": "Low quality text.",
                "quality_score": 0.2,
            }
        ]
        self.assertEqual(generate_qa_pairs(chunks, min_quality=0.8), [])


if __name__ == "__main__":
    unittest.main()

