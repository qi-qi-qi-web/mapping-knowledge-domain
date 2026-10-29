from __future__ import annotations

import unittest
from pathlib import Path

from edkg.loader import load_repo

ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_repo(ROOT)
        cls.sources = cls.data.source_by_id

    def test_source_ids_are_unique(self) -> None:
        ids = [source.get("id") for source in self.data.sources["sources"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_verified_sources_have_evidence(self) -> None:
        for source in self.data.sources["sources"]:
            if source["status"] != "verified":
                continue
            verification = source["verification"]
            self.assertIn("checked_at", verification)
            self.assertNotEqual(verification.get("method"), "not_checked")
            self.assertIsInstance(verification.get("http_status"), int)
            self.assertTrue(200 <= verification["http_status"] < 400)

    def test_candidates_are_not_used(self) -> None:
        for source in self.data.sources["sources"]:
            if source["status"] == "candidate":
                self.assertEqual(source["used_in"], [], source["id"])

    def test_all_fact_sources_are_verified_and_used_in_mvp(self) -> None:
        for fact in self.data.facts:
            source_id = fact["provenance"]["source_id"]
            source = self.sources[source_id]
            self.assertEqual(source["status"], "verified", source_id)
            self.assertIn("mvp", source["used_in"], source_id)

    def test_every_active_source_is_cited(self) -> None:
        cited = {fact["provenance"]["source_id"] for fact in self.data.facts}
        for source in self.data.sources["sources"]:
            if "mvp" in source["used_in"] and source["status"] == "verified":
                self.assertIn(source["id"], cited)


if __name__ == "__main__":
    unittest.main()
