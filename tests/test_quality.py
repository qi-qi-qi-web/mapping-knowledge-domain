"""Tests for the M1-05 quality-evaluation toolkit."""

from __future__ import annotations

import unittest

from edkg.loader import load_repo
from edkg.quality import (
    SAMPLE_SIZE,
    VERDICTS,
    build_sample,
    evaluate_reviews,
)


class QualitySampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_repo()

    def test_sample_is_deterministic_sized_and_stratified(self) -> None:
        first = build_sample(self.data)
        second = build_sample(self.data)
        self.assertEqual(first["sample"]["items"], second["sample"]["items"])
        items = first["sample"]["items"]
        self.assertEqual(SAMPLE_SIZE, len(items))
        self.assertEqual(SAMPLE_SIZE, len({item["sample_id"] for item in items}))
        self.assertEqual(15, len({item["predicate"] for item in items}))
        for item in items:
            self.assertNotIn("fact_id", item)
            self.assertNotIn("confidence", item)
            self.assertTrue(item["subject_label"])
            self.assertTrue(item["object_label"])
            self.assertTrue(item["quote"])
            self.assertIn(item["source_id"], self.data.source_by_id)

    def test_manifest_maps_each_sample_to_its_fact(self) -> None:
        package = build_sample(self.data)
        facts = {str(fact["id"]): fact for fact in self.data.facts}
        manifest = {row["sample_id"]: row["fact_id"] for row in package["manifest"]["items"]}
        items = {item["sample_id"]: item for item in package["sample"]["items"]}
        self.assertEqual(set(items), set(manifest))
        for sample_id, fact_id in manifest.items():
            self.assertIn(fact_id, facts)
            fact = facts[fact_id]
            item = items[sample_id]
            self.assertEqual(fact["subject"], item["subject"])
            self.assertEqual(fact["predicate"], item["predicate"])
            self.assertEqual(fact["object"], item["object"])
            self.assertEqual(fact["provenance"]["quote"], item["quote"])

    def test_all_correct_reviews_pass_gate(self) -> None:
        package = build_sample(self.data)
        sample = package["sample"]
        rows = [
            {"sample_id": item["sample_id"], "verdict": "correct"}
            for item in sample["items"]
        ]
        report = evaluate_reviews(sample, rows, rows)
        self.assertEqual(1.0, report["reviewers"]["a"]["strict_accuracy"])
        self.assertEqual(1.0, report["reviewers"]["b"]["strict_accuracy"])
        self.assertEqual(1.0, report["agreement"]["kappa"])
        self.assertEqual(0, report["agreement"]["disagreements"])
        self.assertTrue(report["gate"]["passed"])
        self.assertEqual(1.0, report["inter_reviewer_prf"]["a_as_reference_b_as_prediction"]["macro_f1"])

    def test_partial_is_half_and_invalid_verdict_is_rejected(self) -> None:
        package = build_sample(self.data)
        sample = package["sample"]
        a_rows = [
            {"sample_id": item["sample_id"], "verdict": "correct"}
            for item in sample["items"]
        ]
        b_rows = [
            {"sample_id": item["sample_id"], "verdict": "partial"}
            for item in sample["items"]
        ]
        report = evaluate_reviews(sample, a_rows, b_rows)
        self.assertEqual(0.0, report["reviewers"]["b"]["strict_accuracy"])
        self.assertEqual(0.5, report["reviewers"]["b"]["lenient_accuracy"])
        self.assertFalse(report["gate"]["passed"])

        bad_rows = [dict(row) for row in a_rows]
        bad_rows[0]["verdict"] = "not-a-verdict"
        with self.assertRaises(ValueError):
            evaluate_reviews(sample, bad_rows, b_rows)
        with self.assertRaises(ValueError):
            evaluate_reviews(sample, a_rows[:-1], b_rows)


if __name__ == "__main__":
    unittest.main()
