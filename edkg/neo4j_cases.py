"""Reference results for the ten documented Cypher use cases.

The Neo4j export is a projection of the JSONL graph.  These functions
compute the same result sets directly from ``RepoData`` so the committed
``queries/expected.json`` fixtures can be checked without a running Neo4j
server.  The Cypher files and these reference functions intentionally share
the same case IDs and parameters.
"""

from __future__ import annotations

from typing import Any, Callable

from edkg.loader import RepoData

CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "01_complaint_differentials",
        "file": "01_complaint_differentials.cypher",
        "params": {"complaint_id": "cc.chest_pain"},
    },
    {
        "id": "02_high_risk_conditions",
        "file": "02_high_risk_conditions.cypher",
        "params": {},
    },
    {
        "id": "03_red_flags_for_complaint",
        "file": "03_red_flags_for_complaint.cypher",
        "params": {"complaint_id": "cc.chest_pain"},
    },
    {
        "id": "04_condition_workup",
        "file": "04_condition_workup.cypher",
        "params": {"condition_id": "cond.acute_mi"},
    },
    {
        "id": "05_complaint_workup",
        "file": "05_complaint_workup.cypher",
        "params": {"complaint_id": "cc.dyspnea"},
    },
    {
        "id": "06_treatment_options",
        "file": "06_treatment_options.cypher",
        "params": {"complaint_id": "cc.chest_pain"},
    },
    {
        "id": "07_triage_criteria",
        "file": "07_triage_criteria.cypher",
        "params": {"scale_id": "esi_v4_2005"},
    },
    {
        "id": "08_icd10_coded_conditions",
        "file": "08_icd10_coded_conditions.cypher",
        "params": {},
    },
    {
        "id": "09_condition_evidence",
        "file": "09_condition_evidence.cypher",
        "params": {"condition_id": "cond.aad"},
    },
    {
        "id": "10_source_coverage",
        "file": "10_source_coverage.cypher",
        "params": {},
    },
)

CASE_BY_ID = {str(case["id"]): case for case in CASES}


def _entities(data: RepoData) -> dict[str, dict[str, Any]]:
    return {str(entity["id"]): entity for entity in data.entities}


def _facts(data: RepoData) -> list[dict[str, Any]]:
    return sorted(data.facts, key=lambda item: str(item["id"]))


def _label(entities: dict[str, dict[str, Any]], entity_id: str) -> str:
    return str((entities.get(entity_id) or {}).get("label_zh", entity_id))


def _properties(entities: dict[str, dict[str, Any]], entity_id: str) -> dict[str, Any]:
    return dict((entities.get(entity_id) or {}).get("properties") or {})


def _source(fact: dict[str, Any], key: str, default: Any = None) -> Any:
    return (fact.get("provenance") or {}).get(key, default)


def _qualifier(fact: dict[str, Any], key: str, default: Any = None) -> Any:
    return (fact.get("qualifiers") or {}).get(key, default)


def _complaint_differentials(data: RepoData) -> list[dict[str, Any]]:
    entities = _entities(data)
    rows = []
    for fact in _facts(data):
        if fact.get("predicate") != "MAY_INDICATE":
            continue
        if fact.get("subject") != "cc.chest_pain":
            continue
        condition_id = str(fact["object"])
        rows.append(
            {
                "condition_id": condition_id,
                "label_zh": _label(entities, condition_id),
                "risk": _qualifier(fact, "risk") or _properties(entities, condition_id).get("risk"),
                "icd10": _properties(entities, condition_id).get("icd10"),
                "source_id": _source(fact, "source_id"),
                "quote": _source(fact, "quote"),
            }
        )
    return sorted(rows, key=lambda row: row["condition_id"])


def _high_risk_conditions(data: RepoData) -> list[dict[str, Any]]:
    entities = _entities(data)
    facts = _facts(data)
    rows = []
    for condition_id, entity in sorted(entities.items()):
        if entity.get("type") != "Condition":
            continue
        properties = entity.get("properties") or {}
        if properties.get("risk") != "high":
            continue
        presentations = {
            str(fact["object"])
            for fact in facts
            if fact.get("predicate") == "PRESENTS_WITH" and fact.get("subject") == condition_id
        }
        red_flags = {
            str(fact["object"])
            for fact in facts
            if fact.get("predicate") == "HAS_RED_FLAG" and fact.get("subject") == condition_id
        }
        rows.append(
            {
                "condition_id": condition_id,
                "label_zh": _label(entities, condition_id),
                "icd10": properties.get("icd10"),
                "presentations": len(presentations),
                "red_flags": len(red_flags),
            }
        )
    return rows


def _red_flags_for_complaint(data: RepoData) -> list[dict[str, Any]]:
    entities = _entities(data)
    facts = _facts(data)
    conditions = {
        str(fact["object"])
        for fact in facts
        if fact.get("predicate") == "MAY_INDICATE" and fact.get("subject") == "cc.chest_pain"
    }
    rows = []
    for fact in facts:
        if fact.get("predicate") != "HAS_RED_FLAG" or fact.get("subject") not in conditions:
            continue
        condition_id = str(fact["subject"])
        finding_id = str(fact["object"])
        rows.append(
            {
                "condition_id": condition_id,
                "condition_label": _label(entities, condition_id),
                "finding_id": finding_id,
                "finding_label": _label(entities, finding_id),
                "source_id": _source(fact, "source_id"),
                "quote": _source(fact, "quote"),
            }
        )
    return sorted(rows, key=lambda row: (row["condition_id"], row["finding_id"]))


def _condition_workup(data: RepoData) -> list[dict[str, Any]]:
    entities = _entities(data)
    rows = []
    for fact in _facts(data):
        if fact.get("predicate") != "RECOMMENDED_TEST" or fact.get("subject") != "cond.acute_mi":
            continue
        test_id = str(fact["object"])
        rows.append(
            {
                "test_id": test_id,
                "test_label": _label(entities, test_id),
                "priority": _qualifier(fact, "priority"),
                "timing": _qualifier(fact, "timing"),
                "context": _qualifier(fact, "context"),
                "source_id": _source(fact, "source_id"),
                "quote": _source(fact, "quote"),
            }
        )
    return sorted(rows, key=lambda row: row["test_id"])


def _complaint_workup(data: RepoData) -> list[dict[str, Any]]:
    entities = _entities(data)
    rows = []
    for fact in _facts(data):
        if fact.get("predicate") != "RECOMMENDED_TEST" or fact.get("subject") != "cc.dyspnea":
            continue
        test_id = str(fact["object"])
        rows.append(
            {
                "test_id": test_id,
                "test_label": _label(entities, test_id),
                "priority": _qualifier(fact, "priority"),
                "timing": _qualifier(fact, "timing"),
                "context": _qualifier(fact, "context"),
                "source_id": _source(fact, "source_id"),
                "quote": _source(fact, "quote"),
            }
        )
    return sorted(rows, key=lambda row: row["test_id"])


def _treatment_options(data: RepoData) -> list[dict[str, Any]]:
    entities = _entities(data)
    facts = _facts(data)
    conditions = {
        str(fact["object"])
        for fact in facts
        if fact.get("predicate") == "MAY_INDICATE" and fact.get("subject") == "cc.chest_pain"
    }
    rows = []
    for fact in facts:
        if fact.get("predicate") != "TREATS" or fact.get("object") not in conditions:
            continue
        condition_id = str(fact["object"])
        intervention_id = str(fact["subject"])
        rows.append(
            {
                "condition_id": condition_id,
                "condition_label": _label(entities, condition_id),
                "intervention_id": intervention_id,
                "intervention_label": _label(entities, intervention_id),
                "urgency": _qualifier(fact, "urgency"),
                "context": _qualifier(fact, "context"),
                "source_id": _source(fact, "source_id"),
                "quote": _source(fact, "quote"),
            }
        )
    return sorted(rows, key=lambda row: (row["condition_id"], row["intervention_id"]))


def _triage_criteria(data: RepoData) -> list[dict[str, Any]]:
    entities = _entities(data)
    facts = _facts(data)
    scale_ids = [
        entity_id
        for entity_id, entity in entities.items()
        if entity.get("type") == "TriageScale"
        and (entity.get("properties") or {}).get("scale_id") == "esi_v4_2005"
    ]
    if len(scale_ids) != 1:
        return []
    scale_id = scale_ids[0]
    levels = [
        str(fact["object"])
        for fact in facts
        if fact.get("predicate") == "HAS_LEVEL" and fact.get("subject") == scale_id
    ]
    level_set = set(levels)
    rows = []
    for fact in facts:
        if fact.get("predicate") != "LEVEL_CRITERION" or fact.get("subject") not in level_set:
            continue
        level_id = str(fact["subject"])
        criterion_id = str(fact["object"])
        rows.append(
            {
                "level": _properties(entities, level_id).get("level"),
                "level_label": _label(entities, level_id),
                "criterion_id": criterion_id,
                "criterion_label": _label(entities, criterion_id),
                "criterion_type": _qualifier(fact, "criterion_type"),
                "source_id": _source(fact, "source_id"),
                "quote": _source(fact, "quote"),
            }
        )
    return sorted(rows, key=lambda row: (str(row["level"]), row["criterion_id"]))


def _icd10_coded_conditions(data: RepoData) -> list[dict[str, Any]]:
    entities = _entities(data)
    rows = []
    for condition_id, entity in entities.items():
        if entity.get("type") != "Condition":
            continue
        code = (entity.get("properties") or {}).get("icd10")
        if not code:
            continue
        rows.append(
            {
                "condition_id": condition_id,
                "label_zh": _label(entities, condition_id),
                "icd10": code,
            }
        )
    return sorted(rows, key=lambda row: (str(row["icd10"]), row["condition_id"]))


def _condition_evidence(data: RepoData) -> list[dict[str, Any]]:
    entities = _entities(data)
    rows = []
    for fact in _facts(data):
        subject = str(fact.get("subject"))
        obj = str(fact.get("object"))
        if subject != "cond.aad" and obj != "cond.aad":
            continue
        other_id = obj if subject == "cond.aad" else subject
        rows.append(
            {
                "predicate": fact.get("predicate"),
                "subject_id": subject,
                "object_id": obj,
                "other_id": other_id,
                "other_label": _label(entities, other_id),
                "source_id": _source(fact, "source_id"),
                "quote": _source(fact, "quote"),
            }
        )
    return sorted(rows, key=lambda row: (str(row["predicate"]), row["subject_id"], row["object_id"]))


def _source_coverage(data: RepoData) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for fact in _facts(data):
        source_id = _source(fact, "source_id")
        if not source_id:
            continue
        counts[str(source_id)] = counts.get(str(source_id), 0) + 1
    return [
        {"source_id": source_id, "facts": count}
        for source_id, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


_RUNNERS: dict[str, Callable[[RepoData], list[dict[str, Any]]]] = {
    "01_complaint_differentials": _complaint_differentials,
    "02_high_risk_conditions": _high_risk_conditions,
    "03_red_flags_for_complaint": _red_flags_for_complaint,
    "04_condition_workup": _condition_workup,
    "05_complaint_workup": _complaint_workup,
    "06_treatment_options": _treatment_options,
    "07_triage_criteria": _triage_criteria,
    "08_icd10_coded_conditions": _icd10_coded_conditions,
    "09_condition_evidence": _condition_evidence,
    "10_source_coverage": _source_coverage,
}


def compute_case(data: RepoData, case_id: str) -> list[dict[str, Any]]:
    if case_id not in _RUNNERS:
        raise KeyError(f"unknown query case: {case_id}")
    return _RUNNERS[case_id](data)


def compute_all(data: RepoData) -> dict[str, list[dict[str, Any]]]:
    return {str(case["id"]): compute_case(data, str(case["id"])) for case in CASES}
