from __future__ import annotations

import unittest
from pathlib import Path

from edkg.loader import load_repo
from edkg.stats import compute_stats

ROOT = Path(__file__).resolve().parents[1]


class StatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stats = compute_stats(load_repo(ROOT))

    def test_minimum_m1_size(self) -> None:
        self.assertGreaterEqual(self.stats["entity_count"], 98)
        self.assertGreaterEqual(self.stats["fact_count"], 133)

    def test_provenance_is_complete(self) -> None:
        self.assertEqual(self.stats["provenance_coverage"], 1.0)
        self.assertEqual(self.stats["duplicate_triples"], 0)

    def test_all_facts_are_ai_draft(self) -> None:
        self.assertEqual(self.stats["review_statuses"], {"ai-draft": self.stats["fact_count"]})
        self.assertEqual(self.stats["assertion_types"], {"explicit": self.stats["fact_count"]})

    def test_three_active_sources_are_cited(self) -> None:
        self.assertEqual(
            set(self.stats["cited_sources"]),
            {
                "src.cn.chest_pain.2019",
                "src.cn.triage.2018",
                "src.us.ahrq.esi.v4.2005",
            },
        )
        self.assertIn("TriageCriterion", self.stats["entity_types"])


if __name__ == "__main__":
    unittest.main()
