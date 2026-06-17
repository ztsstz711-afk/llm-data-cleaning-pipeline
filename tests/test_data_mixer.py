import unittest

from src.data_mixer import sample_mixture


class DataMixerTests(unittest.TestCase):
    def test_zero_ratio_excludes_a_domain(self) -> None:
        records = [
            {
                "source_id": "a",
                "text": "Record A",
                "quality_score": 0.9,
                "metadata": {"domain": "docs", "language": "en"},
            },
            {
                "source_id": "b",
                "text": "Record B",
                "quality_score": 0.9,
                "metadata": {"domain": "ads", "language": "en"},
            },
        ]
        ratios = {
            "source": {"default": 1.0},
            "domain": {"docs": 1.0, "ads": 0.0},
            "language": {"default": 1.0},
            "quality_level": {"default": 1.0},
        }
        sampled = sample_mixture(records, ratios, sample_size=2, seed=1)
        self.assertEqual([record["source_id"] for record in sampled], ["a"])

    def test_sampler_adds_mixture_metadata(self) -> None:
        records = [{"source_id": "a", "text": "Record", "quality_score": 0.8}]
        sampled = sample_mixture(records, {}, sample_size=1)
        self.assertEqual(sampled[0]["metadata"]["quality_level"], "high")
        self.assertIn("domain", sampled[0]["metadata"])


if __name__ == "__main__":
    unittest.main()

