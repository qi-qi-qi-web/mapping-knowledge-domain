from __future__ import annotations

import copy
import unittest
from pathlib import Path
from typing import Callable

from edkg.loader import RepoData, load_repo
from edkg.validate import validate_repo

ROOT = Path(__file__).resolve().parents[1]


def _mutated(mutator: Callable[[dict, dict, list, list], None]) -> RepoData:
    data = load_repo(ROOT)
    schema = copy.deepcopy(data.schema)
    sources = copy.deepcopy(data.sources)
    entities = copy.deepcopy(data.entities)
    facts = copy.deepcopy(data.facts)
    mutator(schema, sources, entities, facts)
    return RepoData(ROOT, schema, sources, entities, facts)


def _codes(report) -> set[str]:
    return {issue.code for issue in report.errors}


class ValidateTests(unittest.TestCase):
    def test_repository_is_valid_in_strict_mode(self) -> None:
        report = validate_repo(load_repo(ROOT), strict=True)
        self.assertTrue(report.ok(strict=True), [issue.to_dict() for issue in report.errors])
        self.assertEqual(report.counts["entities"], len(load_repo(ROOT).entities))
        self.assertGreaterEqual(report.counts["facts"], 100)

    def test_missing_quote_is_error(self) -> None:
        def mutate(schema, sources, entities, facts):
            facts[0]["provenance"].pop("quote")

        report = validate_repo(_mutated(mutate))
        self.assertIn("provenance.quote", _codes(report))

    def test_candidate_source_cannot_be_cited(self) -> None:
        def mutate(schema, sources, entities, facts):
            facts[0]["provenance"]["source_id"] = "src.github.ddxplus"

        report = validate_repo(_mutated(mutate))
        self.assertTrue({"provenance.source_status", "provenance.source_usage"} & _codes(report))

    def test_candidate_cannot_be_marked_used(self) -> None:
        def mutate(schema, sources, entities, facts):
            for source in sources["sources"]:
                if source["id"] == "src.github.ddxplus":
                    source["used_in"] = ["mvp"]

        report = validate_repo(_mutated(mutate))
        self.assertIn("source.candidate_used", _codes(report))

    def test_wrong_domain_is_error(self) -> None:
        def mutate(schema, sources, entities, facts):
            facts[0]["subject"] = "test.ecg_12lead"

        report = validate_repo(_mutated(mutate))
        self.assertIn("fact.domain", _codes(report))

    def test_duplicate_triple_is_error(self) -> None:
        def mutate(schema, sources, entities, facts):
            duplicate = copy.deepcopy(facts[0])
            duplicate["id"] = "fact.chest_pain.may_indicate.acs_duplicate"
            facts.append(duplicate)

        report = validate_repo(_mutated(mutate))
        self.assertIn("fact.duplicate_triple", _codes(report))

    def test_self_loop_is_error(self) -> None:
        def mutate(schema, sources, entities, facts):
            facts.append(
                {
                    "id": "fact.acs.differentiated_from.self",
                    "subject": "cond.acs",
                    "predicate": "DIFFERENTIATED_FROM",
                    "object": "cond.acs",
                    "qualifiers": {},
                    "provenance": copy.deepcopy(facts[0]["provenance"]),
                }
            )

        report = validate_repo(_mutated(mutate))
        self.assertIn("fact.self_loop", _codes(report))

    def test_unknown_object_is_error(self) -> None:
        def mutate(schema, sources, entities, facts):
            facts[0]["object"] = "cond.not_exists"

        report = validate_repo(_mutated(mutate))
        self.assertIn("fact.object", _codes(report))

    def test_long_quote_is_error(self) -> None:
        def mutate(schema, sources, entities, facts):
            facts[0]["provenance"]["quote"] = "引" * 301

        report = validate_repo(_mutated(mutate))
        self.assertIn("provenance.quote_long", _codes(report))


if __name__ == "__main__":
    unittest.main()
