from __future__ import annotations

import csv
import json
import shutil
import unittest
from pathlib import Path

from edkg.loader import load_repo
from edkg.neo4j import TYPE_SLUGS, write_export
from edkg.neo4j_cases import CASES, compute_all

ROOT = Path(__file__).resolve().parents[1]
QUERIES = ROOT / "queries"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Neo4jExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_repo(ROOT)
        cls.out = ROOT / "data" / "raw" / "neo4j-test"
        shutil.rmtree(cls.out, ignore_errors=True)
        cls.addClassCleanup(lambda: shutil.rmtree(cls.out, ignore_errors=True))
        cls.counts = write_export(cls.data, cls.out)

    def test_export_counts(self) -> None:
        self.assertEqual(
            self.counts,
            {
                "nodes": 135,
                "relationships": 192,
                "node_types": 13,
                "predicates": 15,
            },
        )

    def test_node_csvs_cover_every_entity(self) -> None:
        ids: set[str] = set()
        total = 0
        for label, slug in TYPE_SLUGS.items():
            rows = _read_csv(self.out / "import" / f"nodes_{slug}.csv")
            self.assertTrue(rows, label)
            for row in rows:
                self.assertEqual(row["type"], label)
                self.assertTrue(row["id"])
                self.assertNotIn("None", row.values())
                ids.add(row["id"])
            total += len(rows)
        self.assertEqual(total, 135)
        self.assertEqual(len(ids), 135)

    def test_relationship_csvs_cover_every_fact(self) -> None:
        fact_ids: list[str] = []
        for path in sorted((self.out / "import").glob("rels_*.csv")):
            for row in _read_csv(path):
                self.assertTrue(row["fact_id"])
                self.assertTrue(row["subject"])
                self.assertTrue(row["object"])
                self.assertTrue(row["source_id"])
                fact_ids.append(row["fact_id"])
        self.assertEqual(len(fact_ids), 192)
        self.assertEqual(len(set(fact_ids)), 192)

    def test_import_script_is_static_and_reset_free(self) -> None:
        script = (self.out / "import.cypher").read_text(encoding="utf-8")
        self.assertEqual(script.count("LOAD CSV WITH HEADERS"), 28)
        self.assertIn("MERGE (n:Entity:Condition {id: row.id})", script)
        self.assertIn("MERGE (s)-[r:MAY_INDICATE {fact_id: row.fact_id}]->(o)", script)
        self.assertIn("file:///nodes_condition.csv", script)
        self.assertNotIn("apoc.", script.lower())
        for forbidden in ("DELETE", "DETACH DELETE", "CREATE (", "SET n = row"):
            self.assertNotIn(forbidden, script)

    def test_ten_cases_match_expected_fixtures(self) -> None:
        cases = json.loads((QUERIES / "cases.json").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(len(cases), 10)
        self.assertEqual({case["id"] for case in cases}, {case["id"] for case in CASES})
        expected = json.loads((QUERIES / "expected.json").read_text(encoding="utf-8"))
        actual = compute_all(self.data)
        self.assertEqual(set(actual), set(expected))
        for case in cases:
            case_id = case["id"]
            self.assertTrue((QUERIES / case["file"]).is_file())
            self.assertEqual(actual[case_id], expected[case_id], case_id)

    def test_queries_are_read_only_and_parameterized(self) -> None:
        cases = json.loads((QUERIES / "cases.json").read_text(encoding="utf-8"))["cases"]
        forbidden = ("CREATE", "MERGE", "DELETE", "SET", "REMOVE", "DROP", "CALL")
        for case in cases:
            text = (QUERIES / case["file"]).read_text(encoding="utf-8")
            for word in forbidden:
                self.assertNotIn(word, text.upper(), f"{case['id']} contains {word}")
            for param in (case.get("params") or {}):
                self.assertIn(f"${param}", text)

    def test_export_is_deterministic(self) -> None:
        other = ROOT / "data" / "raw" / "neo4j-test-other"
        shutil.rmtree(other, ignore_errors=True)
        try:
            write_export(self.data, other)
            first = {
                path.relative_to(self.out): path.read_bytes()
                for path in self.out.rglob("*")
                if path.is_file()
            }
            second = {
                path.relative_to(other): path.read_bytes()
                for path in other.rglob("*")
                if path.is_file()
            }
            self.assertEqual(first, second)
        finally:
            shutil.rmtree(other, ignore_errors=True)

    def test_key_case_rows_are_sane(self) -> None:
        expected = json.loads((QUERIES / "expected.json").read_text(encoding="utf-8"))
        self.assertEqual(len(expected["01_complaint_differentials"]), 9)
        self.assertEqual(
            {row["condition_id"] for row in expected["08_icd10_coded_conditions"]},
            {
                "cond.acute_mi",
                "cond.aad",
                "cond.ape",
                "cond.tension_pneumothorax",
                "cond.stable_cad",
                "cond.gerd",
                "cond.costochondritis",
                "cond.neurosis",
            },
        )
        self.assertEqual(len(expected["10_source_coverage"]), 6)
        self.assertEqual(sum(row["facts"] for row in expected["10_source_coverage"]), 192)


if __name__ == "__main__":
    unittest.main()
