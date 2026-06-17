import unittest

from src.rag_chunker import build_chunks


class RagChunkerTests(unittest.TestCase):
    def test_fixed_length_chunks_include_overlap_and_metadata(self) -> None:
        records = [
            {
                "source_id": "doc-1",
                "text": "abcdefghijklmnopqrstuvwxyz",
                "metadata": {"domain": "demo"},
            }
        ]
        chunks = build_chunks(records, chunk_size=10, overlap=2, quality_threshold=0.0)
        self.assertEqual(chunks[0]["text"], "abcdefghij")
        self.assertTrue(chunks[1]["text"].startswith("ij"))
        self.assertEqual(chunks[0]["source_id"], "doc-1")
        self.assertIn("quality_score", chunks[0])
        self.assertEqual(chunks[0]["metadata"]["domain"], "demo")

    def test_low_quality_chunks_can_be_filtered(self) -> None:
        records = [{"source_id": "doc-1", "text": "short text"}]
        chunks = build_chunks(records, 100, 0, quality_threshold=1.0)
        self.assertEqual(chunks, [])


if __name__ == "__main__":
    unittest.main()

