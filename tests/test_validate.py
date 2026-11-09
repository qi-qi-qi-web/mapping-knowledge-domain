from __future__ import annotations

import copy
import unittest
from pathlib import Path
from typing import Callable

from edkg.loader import RepoData, load_repo
from edkg.validate import validate_repo

ROOT = Path(__file__).resolve().parents[1]


def _mutated(
    mutator: Callable[[dict, dict, list, list], None] | None = None,
    registry_mutator: Callable[[dict], None] | None = None,
) -> RepoData:
    data = load_repo(ROOT)
    schema = copy.deepcopy(data.schema)
    sources = copy.deepcopy(data.sources)
    entities = copy.deepcopy(data.entities)
    facts = copy.deepcopy(data.facts)
    icd10 = copy.deepcopy(data.icd10)
    if mutator is not None:
        mutator(schema, sources, entities, facts)
    if registry_mutator is not None:
        registry_mutator(icd10)
    return RepoData(ROOT, schema, sources, entities, facts, icd10=icd10)


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

    def test_coded_condition_requires_registry_entry(self) -> None:
        def drop_entry(registry):
            registry["entries"] = [
                entry
                for entry in registry["entries"]
                if entry["condition_id"] != "cond.acute_mi"
            ]

        report = validate_repo(_mutated(registry_mutator=drop_entry))
        self.assertIn("icd10.missing", _codes(report))

    def test_condition_code_must_match_registry(self) -> None:
        def change_code(registry):
            entry = next(
                item for item in registry["entries"] if item["condition_id"] == "cond.acute_mi"
            )
            entry["code"] = "I21.4"

        report = validate_repo(_mutated(registry_mutator=change_code))
        self.assertIn("icd10.code_mismatch", _codes(report))

    def test_icd10_source_must_be_verified_and_used(self) -> None:
        def candidate(schema, sources, entities, facts):
            source = next(
                item for item in sources["sources"] if item["id"] == "src.who.icd10.2019"
            )
            source["status"] = "candidate"
            source["used_in"] = ["m1"]

        report = validate_repo(_mutated(candidate))
        self.assertIn("icd10.source_status", _codes(report))

        def unused(schema, sources, entities, facts):
            source = next(
                item for item in sources["sources"] if item["id"] == "src.who.icd10.2019"
            )
            source["used_in"] = []

        report = validate_repo(_mutated(unused))
        self.assertIn("icd10.source_usage", _codes(report))

    def test_no_single_code_condition_must_not_have_code(self) -> None:
        def mutate(schema, sources, entities, facts):
            condition = next(item for item in entities if item["id"] == "cond.acs")
            condition["properties"]["icd10"] = "I24.9"

        report = validate_repo(_mutated(mutate))
        self.assertIn("icd10.no_single_code", _codes(report))

    def test_minimum_coded_conditions_is_enforced(self) -> None:
        def raise_minimum(schema, sources, entities, facts):
            schema["constraints"]["min_coded_conditions"] = 9

        report = validate_repo(_mutated(raise_minimum))
        self.assertIn("icd10.minimum", _codes(report))

    def test_condition_icd10_format_is_checked(self) -> None:
        def mutate(schema, sources, entities, facts):
            condition = next(item for item in entities if item["id"] == "cond.acute_mi")
            condition["properties"]["icd10"] = "I219"

        report = validate_repo(_mutated(mutate))
        self.assertIn("icd10.code_format", _codes(report))


if __name__ == "__main__":
    unittest.main()
