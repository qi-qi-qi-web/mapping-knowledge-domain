"""Graph statistics for reports and CI."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .loader import RepoData


def compute_stats(data: RepoData) -> dict[str, Any]:
    entity_types = Counter(str(item.get("type")) for item in data.entities)
    predicates = Counter(str(item.get("predicate")) for item in data.facts)
    review_statuses = Counter(
        str((item.get("provenance") or {}).get("review_status")) for item in data.facts
    )
    assertion_types = Counter(
        str((item.get("provenance") or {}).get("assertion_type")) for item in data.facts
    )
    source_usage = Counter(
        f"{source.get('id')}:{','.join(source.get('used_in') or [])}"
        for source in data.sources.get("sources", [])
    )
    source_status = Counter(
        str(source.get("status")) for source in data.sources.get("sources", [])
    )
    cited_sources = Counter(
        str((item.get("provenance") or {}).get("source_id")) for item in data.facts
    )
    triples = [(item.get("subject"), item.get("predicate"), item.get("object")) for item in data.facts]
    provenance_complete = 0
    for fact in data.facts:
        provenance = fact.get("provenance") or {}
        required = ["source_id", "locator", "quote", "confidence", "assertion_type", "review_status"]
        if all(provenance.get(key) not in (None, "") for key in required):
            provenance_complete += 1
    risk_counts = Counter(
        str((item.get("properties") or {}).get("risk"))
        for item in data.entities
        if item.get("type") == "Condition"
    )
    return {
        "schema_version": data.schema.get("version"),
        "source_count": len(data.sources.get("sources", [])),
        "entity_count": len(data.entities),
        "fact_count": len(data.facts),
        "entity_types": dict(sorted(entity_types.items())),
        "predicates": dict(sorted(predicates.items())),
        "source_status": dict(sorted(source_status.items())),
        "source_usage": dict(sorted(source_usage.items())),
        "cited_sources": dict(sorted(cited_sources.items())),
        "review_statuses": dict(sorted(review_statuses.items())),
        "assertion_types": dict(sorted(assertion_types.items())),
        "provenance_complete": provenance_complete,
        "provenance_coverage": round(provenance_complete / len(data.facts), 4)
        if data.facts
        else 0.0,
        "duplicate_triples": len(triples) - len(set(triples)),
        "condition_risk": dict(sorted(risk_counts.items())),
    }


def render_stats_text(stats: dict[str, Any]) -> str:
    lines = [
        f"ED-ConsultKG {stats['schema_version']}",
        f"实体: {stats['entity_count']}  事实: {stats['fact_count']}  来源: {stats['source_count']}",
        f"provenance 完整率: {stats['provenance_coverage']:.1%}",
        f"重复三元组: {stats['duplicate_triples']}",
        "",
        "实体类型:",
    ]
    for key, value in stats["entity_types"].items():
        lines.append(f"  {key}: {value}")
    lines.append("事实谓词:")
    for key, value in stats["predicates"].items():
        lines.append(f"  {key}: {value}")
    lines.append("来源状态:")
    for key, value in stats["source_status"].items():
        lines.append(f"  {key}: {value}")
    lines.append("事实引用来源:")
    for key, value in stats["cited_sources"].items():
        lines.append(f"  {key}: {value}")
    lines.append("审核状态:")
    for key, value in stats["review_statuses"].items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines) + "\n"
