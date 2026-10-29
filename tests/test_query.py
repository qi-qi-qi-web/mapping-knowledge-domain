from __future__ import annotations

import json
import unittest
from pathlib import Path

from edkg.loader import load_repo
from edkg.query import QueryError, query_complaint, render_text

ROOT = Path(__file__).resolve().parents[1]


class QueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_repo(ROOT)
        cls.result = query_complaint(cls.data, "胸痛")

    def test_high_risk_conditions_are_present(self) -> None:
        ids = {item["id"] for item in self.result["conditions"]}
        for expected in ("cond.acs", "cond.aad", "cond.ape", "cond.tension_pneumothorax"):
            self.assertIn(expected, ids)

    def test_chest_pain_triage_levels_are_present(self) -> None:
        ids = {item["id"] for item in self.result["triage"]["levels"]}
        self.assertIn("level.cn4.2", ids)
        self.assertIn("level.cn4.3", ids)

    def test_mdt_is_present(self) -> None:
        ids = {item["id"] for item in self.result["mdt"]}
        self.assertIn("proc.chest_pain_center", ids)

    def test_every_item_has_evidence(self) -> None:
        evidence_ids = {item["id"] for item in self.result["evidence"]}
        for condition in self.result["conditions"]:
            self.assertTrue(condition["may_indicate"]["evidence"])
            for key in ("recommended_tests", "treatments", "dispositions"):
                for item in condition[key]:
                    self.assertTrue(item["evidence"], f"{condition['id']} {key}")
            for item in condition["presentations"] + condition["red_flags"]:
                self.assertTrue(item["evidence"])
        self.assertTrue(evidence_ids)

    def test_all_facts_are_ai_draft(self) -> None:
        self.assertEqual(self.result["review_statuses"], ["ai-draft"])

    def test_json_serializable_and_text_contains_disclaimer(self) -> None:
        payload = json.dumps(self.result, ensure_ascii=False)
        self.assertIn("胸痛", payload)
        text = render_text(self.result)
        self.assertIn("不得用于真实患者诊疗", text)
        self.assertIn("急性冠状动脉综合征", text)

    def test_finding_filter_accepts_alias(self) -> None:
        result = query_complaint(self.data, "胸痛", ["类似心脏因素的胸痛"])
        self.assertIn("类似心脏因素的胸痛", result["query"]["findings"])

    def test_unknown_complaint_raises(self) -> None:
        with self.assertRaises(QueryError):
            query_complaint(self.data, "不存在的胸痛主诉")

    def test_ambiguous_or_non_complaint_rejected(self) -> None:
        with self.assertRaises(QueryError):
            query_complaint(self.data, "动脉血气分析")


if __name__ == "__main__":
    unittest.main()
