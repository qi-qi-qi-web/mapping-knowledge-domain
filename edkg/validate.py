"""Validation rules for the ED-ConsultKG schema, source registry and facts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .loader import RepoData

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class Issue:
    level: str
    code: str
    message: str
    record_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "record_id": self.record_id,
        }


@dataclass
class ValidationReport:
    issues: list[Issue] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def add(self, level: str, code: str, message: str, record_id: str | None = None) -> None:
        self.issues.append(Issue(level, code, message, record_id))

    def error(self, code: str, message: str, record_id: str | None = None) -> None:
        self.add("error", code, message, record_id)

    def warning(self, code: str, message: str, record_id: str | None = None) -> None:
        self.add("warning", code, message, record_id)

    @property
    def errors(self) -> list[Issue]:
        return [item for item in self.issues if item.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [item for item in self.issues if item.level == "warning"]

    def ok(self, strict: bool = False) -> bool:
        return not self.errors and not (strict and self.warnings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok(),
            "strict_ok": self.ok(strict=True),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "counts": self.counts,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_enum(value: Any, enum_name: str, schema: dict[str, Any]) -> bool:
    enums = schema.get("enums", {})
    return enum_name in enums and value in enums[enum_name]


def _validate_properties(
    record: dict[str, Any],
    spec: dict[str, Any],
    schema: dict[str, Any],
    report: ValidationReport,
    record_id: str,
    context: str,
) -> None:
    properties = record.get("properties", {})
    if properties is None:
        properties = {}
    if not isinstance(properties, dict):
        report.error("entity.properties", f"{context}: properties must be an object", record_id)
        return
    allowed = spec.get("properties", {})
    for key in _as_list(spec.get("required")):
        if key in allowed and key not in properties:
            report.error("entity.required_property", f"{context}: missing property {key}", record_id)
    for key, value in properties.items():
        prop_spec = allowed.get(key)
        if not prop_spec:
            report.warning("entity.unknown_property", f"{context}: unknown property {key}", record_id)
            continue
        if value is None:
            if key in _as_list(spec.get("required")):
                report.error(
                    "entity.required_property_null",
                    f"{context}: required property {key} must not be null",
                    record_id,
                )
            continue
        if "enum_ref" in prop_spec and not _check_enum(value, prop_spec["enum_ref"], schema):
            report.error(
                "entity.enum",
                f"{context}: property {key}={value!r} is not in enum {prop_spec['enum_ref']}",
                record_id,
            )
        declared = prop_spec.get("type")
        if declared == "string" and not isinstance(value, str):
            report.error("entity.type", f"{context}: property {key} must be a string", record_id)
        elif declared == "array":
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                report.error(
                    "entity.type", f"{context}: property {key} must be an array of strings", record_id
                )
        elif declared == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                report.error("entity.type", f"{context}: property {key} must be an integer", record_id)
            elif "minimum" in prop_spec and value < prop_spec["minimum"]:
                report.error(
                    "entity.minimum",
                    f"{context}: property {key} must be >= {prop_spec['minimum']}",
                    record_id,
                )
        elif declared == "boolean" and not isinstance(value, bool):
            report.error("entity.type", f"{context}: property {key} must be a boolean", record_id)


def _validate_provenance(
    provenance: Any,
    schema: dict[str, Any],
    sources: dict[str, dict[str, Any]],
    report: ValidationReport,
    record_id: str,
    context: str,
) -> None:
    if not isinstance(provenance, dict):
        report.error("provenance.missing", f"{context}: provenance must be an object", record_id)
        return
    provenance_spec = schema.get("provenance", {})
    required = _as_list(provenance_spec.get("required"))
    optional = set(_as_list(provenance_spec.get("optional")))
    allowed = set(required) | optional
    for key in required:
        value = provenance.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            report.error("provenance.required", f"{context}: missing provenance.{key}", record_id)
    for key in provenance:
        if key not in allowed:
            report.warning("provenance.unknown_field", f"{context}: unknown provenance field {key}", record_id)

    source_id = provenance.get("source_id")
    source = sources.get(str(source_id)) if source_id else None
    if source is None:
        report.error("provenance.source", f"{context}: source_id {source_id!r} is not registered", record_id)
    else:
        if source.get("status") != "verified":
            report.error(
                "provenance.source_status",
                f"{context}: source {source_id} has status {source.get('status')!r}, not 'verified'",
                record_id,
            )
        allowed_usage = _as_list(schema.get("constraints", {}).get("allowed_fact_source_usage"))
        if allowed_usage and not set(allowed_usage) & set(_as_list(source.get("used_in"))):
            report.error(
                "provenance.source_usage",
                f"{context}: source {source_id} is not marked used_in any of {allowed_usage}",
                record_id,
            )

    quote = provenance.get("quote")
    max_len = int(provenance_spec.get("max_quote_length", 300))
    min_len = int(provenance_spec.get("min_quote_length", 4))
    if not isinstance(quote, str) or not quote.strip():
        report.error("provenance.quote", f"{context}: quote is required", record_id)
    else:
        if len(quote) < min_len:
            report.error("provenance.quote_short", f"{context}: quote is too short", record_id)
        if len(quote) > max_len:
            report.error(
                "provenance.quote_long",
                f"{context}: quote has {len(quote)} chars > {max_len}",
                record_id,
            )

    confidence = provenance.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        report.error("provenance.confidence", f"{context}: confidence must be a number", record_id)
    elif not 0 <= float(confidence) <= 1:
        report.error("provenance.confidence_range", f"{context}: confidence must be 0..1", record_id)

    assertion_type = provenance.get("assertion_type")
    if not _check_enum(assertion_type, "assertion_types", {**schema, "enums": {**schema.get("enums", {}), "assertion_types": provenance_spec.get("assertion_types", [])}}):
        report.error(
            "provenance.assertion_type",
            f"{context}: assertion_type {assertion_type!r} is invalid",
            record_id,
        )
    review_status = provenance.get("review_status")
    if not _check_enum(review_status, "review_statuses", {**schema, "enums": {**schema.get("enums", {}), "review_statuses": provenance_spec.get("review_statuses", [])}}):
        report.error(
            "provenance.review_status",
            f"{context}: review_status {review_status!r} is invalid",
            record_id,
        )
    if assertion_type == "inferred" and not _nonempty_str(provenance.get("rationale")):
        report.error("provenance.rationale", f"{context}: inferred assertion requires rationale", record_id)
    extracted_at = provenance.get("extracted_at")
    if not isinstance(extracted_at, str) or not _DATE.match(extracted_at):
        report.error("provenance.extracted_at", f"{context}: extracted_at must be YYYY-MM-DD", record_id)
    if not _nonempty_str(provenance.get("extracted_by")):
        report.error("provenance.extracted_by", f"{context}: extracted_by is required", record_id)


def validate_repo(data: RepoData, strict: bool = False) -> ValidationReport:
    report = ValidationReport()
    schema = data.schema
    sources = data.source_by_id
    entities: dict[str, dict[str, Any]] = {}
    facts_by_triple: dict[tuple[str, str, str], str] = {}

    report.counts = {
        "sources": len(data.sources.get("sources", [])),
        "entities": len(data.entities),
        "facts": len(data.facts),
    }

    # --- schema ---------------------------------------------------------
    if not _nonempty_str(schema.get("version")):
        report.error("schema.version", "schema.version is required")
    entity_types = schema.get("entity_types", {})
    relation_types = schema.get("relation_types", {})
    enums = schema.get("enums", {})
    if not isinstance(entity_types, dict) or not entity_types:
        report.error("schema.entity_types", "schema.entity_types must be a non-empty object")
        entity_types = {}
    if not isinstance(relation_types, dict) or not relation_types:
        report.error("schema.relation_types", "schema.relation_types must be a non-empty object")
        relation_types = {}
    if not isinstance(schema.get("provenance", {}).get("required"), list):
        report.error("schema.provenance", "schema.provenance.required must be a list")

    for name, spec in entity_types.items():
        if not isinstance(spec, dict):
            report.error("schema.entity", f"entity type {name} must be an object")
            continue
        if not _nonempty_str(spec.get("id_prefix")):
            report.error("schema.entity_prefix", f"entity type {name} is missing id_prefix")
        for prop, prop_spec in (spec.get("properties") or {}).items():
            if isinstance(prop_spec, dict) and "enum_ref" in prop_spec:
                if prop_spec["enum_ref"] not in enums:
                    report.error(
                        "schema.enum_ref",
                        f"entity {name}.{prop} references missing enum {prop_spec['enum_ref']}",
                    )

    for name, spec in relation_types.items():
        if not isinstance(spec, dict):
            report.error("schema.relation", f"relation {name} must be an object")
            continue
        for side in ("domain", "range"):
            values = spec.get(side)
            if not isinstance(values, list) or not values:
                report.error("schema.relation_side", f"relation {name} is missing {side}")
                continue
            for value in values:
                if value not in entity_types:
                    report.error(
                        "schema.relation_entity",
                        f"relation {name}.{side} references unknown entity type {value}",
                    )
        for qualifier, qualifier_spec in (spec.get("qualifiers") or {}).items():
            if isinstance(qualifier_spec, dict) and "enum_ref" in qualifier_spec:
                if qualifier_spec["enum_ref"] not in enums:
                    report.error(
                        "schema.enum_ref",
                        f"relation {name}.{qualifier} references missing enum {qualifier_spec['enum_ref']}",
                    )

    # --- sources --------------------------------------------------------
    raw_sources = data.sources.get("sources", [])
    if not isinstance(raw_sources, list):
        report.error("sources.list", "sources.sources must be a list")
        raw_sources = []
    seen_sources: set[str] = set()
    for source in raw_sources:
        if not isinstance(source, dict):
            report.error("source.record", "each source must be an object")
            continue
        source_id = source.get("id")
        if not _nonempty_str(source_id):
            report.error("source.id", "source.id is required")
            continue
        source_id = str(source_id)
        if source_id in seen_sources:
            report.error("source.duplicate", f"duplicate source id {source_id}", source_id)
        seen_sources.add(source_id)
        for key in ("type", "title", "publisher", "url", "access", "license", "redistribution", "status", "verification"):
            if key not in source:
                report.error("source.required", f"source {source_id} is missing {key}", source_id)
        if not _check_enum(source.get("type"), "source_type", schema):
            report.error("source.type", f"source {source_id} has invalid type", source_id)
        if not _check_enum(source.get("access"), "source_access", schema):
            report.error("source.access", f"source {source_id} has invalid access", source_id)
        if not _check_enum(source.get("status"), "source_status", schema):
            report.error("source.status", f"source {source_id} has invalid status", source_id)
        url = source.get("url")
        if not (isinstance(url, str) and url.startswith(("http://", "https://"))):
            report.error("source.url", f"source {source_id} needs an http(s) URL", source_id)
        if not isinstance(source.get("used_in"), list):
            report.error("source.used_in", f"source {source_id}.used_in must be a list", source_id)
        used_in = _as_list(source.get("used_in"))
        if source.get("status") == "candidate" and used_in:
            report.error(
                "source.candidate_used",
                f"candidate source {source_id} must not be used; used_in={used_in}",
                source_id,
            )
        if source.get("status") == "verified" and not used_in:
            report.warning("source.unused", f"verified source {source_id} has empty used_in", source_id)
        verification = source.get("verification")
        if not isinstance(verification, dict):
            report.error("source.verification", f"source {source_id}.verification must be an object", source_id)
        else:
            if not _nonempty_str(verification.get("checked_at")):
                report.error("source.checked_at", f"source {source_id} missing checked_at", source_id)
            if not _nonempty_str(verification.get("method")):
                report.error("source.method", f"source {source_id} missing verification.method", source_id)
            if source.get("status") == "verified":
                if verification.get("method") == "not_checked":
                    report.error(
                        "source.verified_method",
                        f"verified source {source_id} cannot use method=not_checked",
                        source_id,
                    )
                status = verification.get("http_status")
                if not (isinstance(status, int) and 200 <= status < 400):
                    report.error(
                        "source.http_status",
                        f"verified source {source_id} needs verification.http_status 2xx/3xx",
                        source_id,
                    )

    # --- entities -------------------------------------------------------
    for entity in data.entities:
        if not isinstance(entity, dict):
            report.error("entity.record", "each entity must be an object")
            continue
        entity_id = entity.get("id")
        if not _nonempty_str(entity_id):
            report.error("entity.id", "entity.id is required")
            continue
        entity_id = str(entity_id)
        if entity_id in entities:
            report.error("entity.duplicate", f"duplicate entity id {entity_id}", entity_id)
            continue
        entities[entity_id] = entity
        pattern = schema.get("constraints", {}).get("entity_id_pattern")
        if pattern and not re.match(pattern, entity_id):
            report.error("entity.id_pattern", f"entity id {entity_id} does not match {pattern}", entity_id)
        entity_type = entity.get("type")
        if entity_type not in entity_types:
            report.error("entity.type", f"entity {entity_id} has unknown type {entity_type!r}", entity_id)
            continue
        spec = entity_types[entity_type]
        prefix = spec.get("id_prefix")
        if prefix and not entity_id.startswith(f"{prefix}."):
            report.error(
                "entity.id_prefix",
                f"entity {entity_id} must start with {prefix}.",
                entity_id,
            )
        if not _nonempty_str(entity.get("label_zh")):
            report.error("entity.label", f"entity {entity_id} needs label_zh", entity_id)
        _validate_properties(entity, spec, schema, report, entity_id, f"entity {entity_id}")
        if spec.get("provenance_required"):
            _validate_provenance(
                entity.get("provenance"), schema, sources, report, entity_id, f"entity {entity_id}"
            )
        if entity_type == "TriageLevel":
            scale_id = (entity.get("properties") or {}).get("scale_id")
            scale = entities.get(f"scale.{scale_id}") if scale_id else None
            if scale is None:
                report.error("entity.scale_ref", f"triage level {entity_id} references unknown scale {scale_id}", entity_id)
            care_area_id = (entity.get("properties") or {}).get("care_area_id")
            if care_area_id:
                area = entities.get(str(care_area_id))
                if area is None or area.get("type") != "CareArea":
                    report.error(
                        "entity.care_area_ref",
                        f"triage level {entity_id} references unknown care area {care_area_id}",
                        entity_id,
                    )

    # --- facts ----------------------------------------------------------
    for fact in data.facts:
        if not isinstance(fact, dict):
            report.error("fact.record", "each fact must be an object")
            continue
        fact_id = fact.get("id")
        if not _nonempty_str(fact_id):
            report.error("fact.id", "fact.id is required")
            continue
        fact_id = str(fact_id)
        pattern = schema.get("constraints", {}).get("fact_id_pattern")
        if pattern and not re.match(pattern, fact_id):
            report.error("fact.id_pattern", f"fact id {fact_id} does not match {pattern}", fact_id)
        subject = fact.get("subject")
        obj = fact.get("object")
        predicate = fact.get("predicate")
        if subject not in entities:
            report.error("fact.subject", f"fact {fact_id} subject {subject!r} not found", fact_id)
        if obj not in entities:
            report.error("fact.object", f"fact {fact_id} object {obj!r} not found", fact_id)
        relation = relation_types.get(predicate)
        if relation is None:
            report.error("fact.predicate", f"fact {fact_id} has unknown predicate {predicate!r}", fact_id)
            continue
        if subject in entities and relation.get("domain"):
            subject_type = entities[subject].get("type")
            if subject_type not in relation["domain"]:
                report.error(
                    "fact.domain",
                    f"fact {fact_id}: subject type {subject_type} not in {relation['domain']}",
                    fact_id,
                )
        if obj in entities and relation.get("range"):
            object_type = entities[obj].get("type")
            if object_type not in relation["range"]:
                report.error(
                    "fact.range",
                    f"fact {fact_id}: object type {object_type} not in {relation['range']}",
                    fact_id,
                )
        if subject == obj and schema.get("constraints", {}).get("no_self_loop", True):
            report.error("fact.self_loop", f"fact {fact_id} is a self-loop", fact_id)
        qualifiers = fact.get("qualifiers", {})
        if qualifiers is None:
            qualifiers = {}
        if not isinstance(qualifiers, dict):
            report.error("fact.qualifiers", f"fact {fact_id}.qualifiers must be an object", fact_id)
            qualifiers = {}
        allowed_qualifiers = relation.get("qualifiers", {})
        for key, value in qualifiers.items():
            qualifier_spec = allowed_qualifiers.get(key)
            if qualifier_spec is None:
                report.error("fact.qualifier_unknown", f"fact {fact_id} has unknown qualifier {key}", fact_id)
                continue
            if isinstance(qualifier_spec, dict) and "enum_ref" in qualifier_spec:
                if not _check_enum(value, qualifier_spec["enum_ref"], schema):
                    report.error(
                        "fact.qualifier_enum",
                        f"fact {fact_id}: qualifier {key}={value!r} invalid",
                        fact_id,
                    )
        for key, qualifier_spec in allowed_qualifiers.items():
            if isinstance(qualifier_spec, dict) and qualifier_spec.get("required") and key not in qualifiers:
                report.error("fact.qualifier_required", f"fact {fact_id} is missing qualifier {key}", fact_id)
        _validate_provenance(
            fact.get("provenance"), schema, sources, report, fact_id, f"fact {fact_id}"
        )
        triple = (str(subject), str(predicate), str(obj))
        if schema.get("constraints", {}).get("unique_triple", True):
            if triple in facts_by_triple:
                report.error(
                    "fact.duplicate_triple",
                    f"fact {fact_id} duplicates triple of {facts_by_triple[triple]}",
                    fact_id,
                )
            else:
                facts_by_triple[triple] = fact_id

    return report
