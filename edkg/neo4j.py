"""Deterministic Neo4j CSV/Cypher export for the ED knowledge graph.

The exporter is deliberately dependency-free and only reads ``RepoData``.
It writes one CSV file per entity label and one CSV file per relationship
predicate, plus a static ``import.cypher`` script and a ``setup.cypher``
script.  Generated files are byte-stable so they can be committed and
reviewed like any other data artifact.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from edkg.loader import RepoData

TYPE_SLUGS: dict[str, str] = {
    "ChiefComplaint": "chief_complaint",
    "Condition": "condition",
    "Finding": "finding",
    "Test": "test",
    "Intervention": "intervention",
    "RiskFactor": "risk_factor",
    "TriageScale": "triage_scale",
    "TriageLevel": "triage_level",
    "TriageCriterion": "triage_criterion",
    "CareArea": "care_area",
    "CareProcess": "care_process",
    "Department": "department",
    "Disposition": "disposition",
}

TYPE_PROPERTIES: dict[str, tuple[str, ...]] = {
    "ChiefComplaint": (),
    "Condition": ("condition_kind", "risk", "icd10"),
    "Finding": ("finding_kind", "red_flag"),
    "Test": ("test_kind",),
    "Intervention": ("intervention_kind",),
    "RiskFactor": ("risk_factor_kind",),
    "TriageScale": ("scale_id", "level_count", "notes"),
    "TriageLevel": (
        "scale_id",
        "level",
        "color",
        "response_time",
        "care_area_id",
        "description",
    ),
    "TriageCriterion": ("criterion_kind", "description"),
    "CareArea": ("care_area_kind",),
    "CareProcess": ("process_kind",),
    "Department": ("department_kind",),
    "Disposition": ("disposition_kind",),
}

COMMON_COLUMNS: tuple[str, ...] = ("id", "type", "label_zh", "label_en", "aliases")
RELATIONSHIP_BASE_COLUMNS: tuple[str, ...] = (
    "fact_id",
    "subject",
    "object",
    "source_id",
    "locator",
    "quote",
    "confidence",
    "review_status",
    "assertion_type",
    "extracted_by",
    "extracted_at",
)

_REL_TYPE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return "|".join(str(item) for item in value)
    return str(value)


def _node_rows(data: RepoData) -> dict[str, list[dict[str, str]]]:
    rows: dict[str, list[dict[str, str]]] = {label: [] for label in TYPE_SLUGS}
    for entity in sorted(data.entities, key=lambda item: str(item["id"])):
        entity_type = str(entity.get("type", ""))
        if entity_type not in TYPE_SLUGS:
            raise ValueError(f"unsupported entity type: {entity_type!r}")
        properties = entity.get("properties") or {}
        row = {
            "id": str(entity["id"]),
            "type": entity_type,
            "label_zh": _csv_value(entity.get("label_zh")),
            "label_en": _csv_value(entity.get("label_en")),
            "aliases": _csv_value(entity.get("aliases")),
        }
        for key in TYPE_PROPERTIES[entity_type]:
            row[key] = _csv_value(properties.get(key))
        rows[entity_type].append(row)
    return rows


def _relationship_rows(data: RepoData) -> dict[str, list[dict[str, str]]]:
    by_predicate: dict[str, list[dict[str, str]]] = defaultdict(list)
    entity_ids = {str(entity["id"]) for entity in data.entities}
    for fact in sorted(data.facts, key=lambda item: str(item["id"])):
        predicate = str(fact.get("predicate", ""))
        if not _REL_TYPE.match(predicate):
            raise ValueError(f"unsupported relationship predicate: {predicate!r}")
        subject = str(fact.get("subject", ""))
        obj = str(fact.get("object", ""))
        if subject not in entity_ids or obj not in entity_ids:
            raise ValueError(f"fact {fact.get('id')} has a missing endpoint")
        provenance = fact.get("provenance") or {}
        qualifiers = fact.get("qualifiers") or {}
        row: dict[str, str] = {
            "fact_id": str(fact["id"]),
            "subject": subject,
            "object": obj,
        }
        for key in RELATIONSHIP_BASE_COLUMNS[3:]:
            row[key] = _csv_value(provenance.get(key))
        for key in sorted(qualifiers):
            row[key] = _csv_value(qualifiers.get(key))
        by_predicate[predicate].append(row)
    return dict(by_predicate)


def _columns_for_rows(rows: Iterable[dict[str, str]], base: Iterable[str]) -> list[str]:
    columns = list(base)
    seen = set(columns)
    for row in rows:
        for key in row:
            if key not in seen:
                columns.append(key)
                seen.add(key)
    return columns


def _write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _render_set(row_alias: str, columns: list[str], target: str) -> str:
    parts = []
    for column in columns:
        value = f"{row_alias}.{column}"
        parts.append(f"    {target}.{column} = CASE WHEN {value} = '' THEN null ELSE {value} END")
    return "SET " + ",\n".join(parts)


def _render_node_import(
    entity_type: str,
    slug: str,
    columns: list[str],
) -> str:
    set_clause = _render_set("row", columns, "n")
    return (
        f"// {entity_type}: {slug}\n"
        f"LOAD CSV WITH HEADERS FROM 'file:///nodes_{slug}.csv' AS row\n"
        f"MERGE (n:Entity:{entity_type} {{id: row.id}})\n"
        f"{set_clause};\n"
    )


def _render_relationship_import(
    predicate: str,
    columns: list[str],
) -> str:
    set_clause = _render_set("row", columns, "r")
    filename = f"rels_{predicate.lower()}.csv"
    return (
        f"// {predicate}\n"
        f"LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row\n"
        f"MATCH (s:Entity {{id: row.subject}}), (o:Entity {{id: row.object}})\n"
        f"MERGE (s)-[r:{predicate} {{fact_id: row.fact_id}}]->(o)\n"
        f"{set_clause};\n"
    )


def _setup_script() -> str:
    return (
        "// Generated by edkg.neo4j; run once before import.cypher.\n"
        "CREATE CONSTRAINT entity_id IF NOT EXISTS "
        "FOR (n:Entity) REQUIRE n.id IS UNIQUE;\n"
        "CREATE INDEX condition_risk IF NOT EXISTS "
        "FOR (n:Condition) ON (n.risk);\n"
        "CREATE INDEX condition_icd10 IF NOT EXISTS "
        "FOR (n:Condition) ON (n.icd10);\n"
        "CREATE INDEX triage_scale_id IF NOT EXISTS "
        "FOR (n:TriageScale) ON (n.scale_id);\n"
    )


def write_export(data: RepoData, out_dir: str | Path) -> dict[str, int]:
    """Write a deterministic Neo4j export and return row/file counts."""

    out = Path(out_dir)
    import_dir = out / "import"
    import_dir.mkdir(parents=True, exist_ok=True)
    for stale in import_dir.glob("*.csv"):
        stale.unlink()

    node_rows = _node_rows(data)
    relationship_rows = _relationship_rows(data)

    node_columns: dict[str, list[str]] = {}
    for entity_type, rows in node_rows.items():
        slug = TYPE_SLUGS[entity_type]
        columns = list(COMMON_COLUMNS) + list(TYPE_PROPERTIES[entity_type])
        node_columns[entity_type] = columns
        _write_csv(import_dir / f"nodes_{slug}.csv", rows, columns)

    rel_columns: dict[str, list[str]] = {}
    for predicate, rows in sorted(relationship_rows.items()):
        columns = _columns_for_rows(rows, RELATIONSHIP_BASE_COLUMNS)
        rel_columns[predicate] = columns
        _write_csv(import_dir / f"rels_{predicate.lower()}.csv", rows, columns)

    node_script = [
        "// Generated by edkg.neo4j; copy neo4j/import/*.csv to Neo4j's import directory.",
        f"// Entity rows: {sum(len(rows) for rows in node_rows.values())}",
        "",
    ]
    for entity_type in sorted(node_rows):
        node_script.append(
            _render_node_import(entity_type, TYPE_SLUGS[entity_type], node_columns[entity_type])
        )

    relationship_script = [
        "// Generated by edkg.neo4j; run after import.cypher.",
        f"// Relationship rows: {sum(len(rows) for rows in relationship_rows.values())}",
        "",
    ]
    for predicate in sorted(relationship_rows):
        relationship_script.append(_render_relationship_import(predicate, rel_columns[predicate]))

    (out / "setup.cypher").write_text(_setup_script(), encoding="utf-8", newline="\n")
    (out / "import.cypher").write_text("\n".join(node_script + relationship_script), encoding="utf-8", newline="\n")

    return {
        "nodes": sum(len(rows) for rows in node_rows.values()),
        "relationships": sum(len(rows) for rows in relationship_rows.values()),
        "node_types": len(node_rows),
        "predicates": len(relationship_rows),
    }
