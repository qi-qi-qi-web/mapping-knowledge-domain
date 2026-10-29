"""Read-only graph queries used by the M0 agent-facing CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .loader import RepoData


class QueryError(ValueError):
    """Raised when a query cannot be answered from the current graph."""


def _norm(value: str) -> str:
    return (value or "").strip().casefold()


class Graph:
    def __init__(self, data: RepoData) -> None:
        self.data = data
        self.entities: dict[str, dict[str, Any]] = {
            str(item["id"]): item for item in data.entities if item.get("id")
        }
        self.facts: list[dict[str, Any]] = data.facts
        self.out: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.incoming_index: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.by_predicate: dict[str, list[dict[str, Any]]] = {}
        for fact in self.facts:
            subject = str(fact.get("subject"))
            predicate = str(fact.get("predicate"))
            obj = str(fact.get("object"))
            self.out.setdefault((subject, predicate), []).append(fact)
            self.incoming_index.setdefault((obj, predicate), []).append(fact)
            self.by_predicate.setdefault(predicate, []).append(fact)

    # -- lookups ---------------------------------------------------------
    def entity(self, entity_id: str) -> dict[str, Any] | None:
        return self.entities.get(entity_id)

    def label(self, entity_id: str) -> str:
        entity = self.entity(entity_id)
        return str(entity.get("label_zh")) if entity else entity_id

    def resolve(self, text: str, allowed_types: Iterable[str] | None = None) -> dict[str, Any]:
        wanted = _norm(text)
        allowed = set(allowed_types) if allowed_types else None
        exact: list[dict[str, Any]] = []
        alias_hits: list[dict[str, Any]] = []
        for entity in self.entities.values():
            if allowed and entity.get("type") not in allowed:
                continue
            labels = [entity.get("label_zh"), entity.get("label_en")]
            aliases = entity.get("aliases") or []
            if any(_norm(str(label)) == wanted for label in labels if label):
                exact.append(entity)
            elif any(_norm(str(alias)) == wanted for alias in aliases):
                alias_hits.append(entity)
        candidates = exact or alias_hits
        if not candidates:
            raise QueryError(f"未收录的实体: {text!r}")
        if len(candidates) > 1:
            ids = ", ".join(str(item.get("id")) for item in candidates)
            raise QueryError(f"实体 {text!r} 有歧义，请用 ID 指定: {ids}")
        return candidates[0]

    def outgoing(self, subject: str, predicate: str) -> list[dict[str, Any]]:
        return list(self.out.get((subject, predicate), []))

    def incoming(self, obj: str, predicate: str) -> list[dict[str, Any]]:
        return list(self.incoming_index.get((obj, predicate), []))


@dataclass
class EvidenceBook:
    items: list[dict[str, Any]] = field(default_factory=list)
    _keys: dict[tuple[str, str, str], str] = field(default_factory=dict)

    def add(self, provenance: dict[str, Any]) -> str:
        source_id = str(provenance.get("source_id", ""))
        locator = str(provenance.get("locator", ""))
        quote = str(provenance.get("quote", ""))
        key = (source_id, locator, quote)
        if key not in self._keys:
            evidence_id = f"ev{len(self.items) + 1}"
            self._keys[key] = evidence_id
            self.items.append(
                {
                    "id": evidence_id,
                    "source_id": source_id,
                    "locator": locator,
                    "quote": quote,
                    "review_status": provenance.get("review_status"),
                    "confidence": provenance.get("confidence"),
                }
            )
        return self._keys[key]


def _evidence_ids(facts: Iterable[dict[str, Any]], book: EvidenceBook) -> list[str]:
    ids: list[str] = []
    for fact in facts:
        evidence_id = book.add(fact.get("provenance") or {})
        if evidence_id not in ids:
            ids.append(evidence_id)
    return ids


def _relation_items(
    graph: Graph,
    facts: list[dict[str, Any]],
    book: EvidenceBook,
    id_field: str = "object",
    extra: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for fact in facts:
        obj = str(fact.get(id_field))
        item: dict[str, Any] = {
            "id": obj,
            "label": graph.label(obj),
            "evidence": _evidence_ids([fact], book),
        }
        qualifiers = fact.get("qualifiers") or {}
        if qualifiers:
            item["qualifiers"] = qualifiers
        if extra:
            item.update(extra)
        items.append(item)
    return items


def query_complaint(
    data: RepoData,
    complaint_text: str,
    finding_texts: Iterable[str] | None = None,
) -> dict[str, Any]:
    graph = Graph(data)
    book = EvidenceBook()
    complaint = graph.resolve(complaint_text, allowed_types=["ChiefComplaint"])
    complaint_id = str(complaint["id"])

    finding_ids: list[str] = []
    for finding_text in finding_texts or []:
        finding = graph.resolve(finding_text, allowed_types=["Finding"])
        finding_ids.append(str(finding["id"]))

    condition_facts = graph.outgoing(complaint_id, "MAY_INDICATE")
    if not condition_facts:
        raise QueryError(f"主诉 {graph.label(complaint_id)} 尚未关联任何疾病")

    conditions: list[dict[str, Any]] = []
    all_finding_ids = set(finding_ids)
    for condition_fact in condition_facts:
        condition_id = str(condition_fact.get("object"))
        condition = graph.entity(condition_id) or {}
        presentation_facts = graph.outgoing(condition_id, "PRESENTS_WITH")
        red_flag_facts = graph.outgoing(condition_id, "HAS_RED_FLAG")
        differential_facts = graph.outgoing(condition_id, "DIFFERENTIATED_FROM")
        reverse_differential_facts = graph.incoming(condition_id, "DIFFERENTIATED_FROM")
        distinguished_facts = graph.outgoing(condition_id, "DISTINGUISHED_BY")
        test_facts = graph.outgoing(condition_id, "RECOMMENDED_TEST")
        treatment_facts = graph.incoming(condition_id, "TREATS")
        disposition_facts = graph.outgoing(condition_id, "TYPICAL_DISPOSITION")
        risk_facts = graph.outgoing(condition_id, "HAS_RISK_FACTOR")
        consult_facts = graph.outgoing(condition_id, "CONSULT")

        for fact in presentation_facts + red_flag_facts + distinguished_facts:
            all_finding_ids.add(str(fact.get("object")))

        conditions.append(
            {
                "id": condition_id,
                "label": graph.label(condition_id),
                "risk": (condition.get("properties") or {}).get("risk"),
                "may_indicate": {
                    "risk": (condition_fact.get("qualifiers") or {}).get("risk"),
                    "evidence": _evidence_ids([condition_fact], book),
                },
                "presentations": _relation_items(graph, presentation_facts, book),
                "red_flags": _relation_items(graph, red_flag_facts, book),
                "differentiated_from": _relation_items(graph, differential_facts, book)
                + _relation_items(graph, reverse_differential_facts, book, id_field="subject"),
                "distinguished_by": _relation_items(graph, distinguished_facts, book),
                "recommended_tests": _relation_items(graph, test_facts, book),
                "treatments": [
                    {
                        "id": str(fact.get("subject")),
                        "label": graph.label(str(fact.get("subject"))),
                        "qualifiers": fact.get("qualifiers") or {},
                        "evidence": _evidence_ids([fact], book),
                    }
                    for fact in treatment_facts
                ],
                "dispositions": _relation_items(graph, disposition_facts, book),
                "risk_factors": _relation_items(graph, risk_facts, book),
                "consultations": _relation_items(graph, consult_facts, book),
            }
        )

    # Deduplicate each condition's differential list (symmetric edges may be
    # asserted in either direction, but must not appear twice for one condition).
    for condition in conditions:
        unique: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for item in condition["differentiated_from"]:
            if item["id"] in seen_ids:
                continue
            seen_ids.add(item["id"])
            unique.append(item)
        condition["differentiated_from"] = unique

    chief_tests = _relation_items(graph, graph.outgoing(complaint_id, "RECOMMENDED_TEST"), book)

    # Triage levels whose criteria intersect the conditions/findings in this result.
    relevant_ids = {condition["id"] for condition in conditions} | all_finding_ids
    for entity in graph.entities.values():
        if entity.get("type") == "Finding" and "胸痛" in str(entity.get("label_zh", "")):
            relevant_ids.add(str(entity["id"]))
    level_entities = [
        entity for entity in graph.entities.values() if entity.get("type") == "TriageLevel"
    ]
    level_entities.sort(
        key=lambda item: (
            str((item.get("properties") or {}).get("scale_id", "")),
            99 if (item.get("properties") or {}).get("level") == "non_emergency"
            else int((item.get("properties") or {}).get("level", 99)),
        )
    )
    triage_levels: list[dict[str, Any]] = []
    for level in level_entities:
        level_id = str(level["id"])
        criteria_facts = graph.outgoing(level_id, "LEVEL_CRITERION")
        matched = [
            fact for fact in criteria_facts if str(fact.get("object")) in relevant_ids
        ]
        if not matched:
            continue
        properties = level.get("properties") or {}
        assigned = graph.outgoing(level_id, "ASSIGNED_TO")
        triage_levels.append(
            {
                "id": level_id,
                "label": graph.label(level_id),
                "color": properties.get("color"),
                "response_time": properties.get("response_time"),
                "description": properties.get("description"),
                "care_area": [
                    {"id": str(fact.get("object")), "label": graph.label(str(fact.get("object")))}
                    for fact in assigned
                ],
                "matched_criteria": [
                    {
                        "id": str(fact.get("object")),
                        "label": graph.label(str(fact.get("object"))),
                        "criterion_type": (fact.get("qualifiers") or {}).get("criterion_type"),
                        "evidence": _evidence_ids([fact], book),
                    }
                    for fact in matched
                ],
            }
        )

    mdt: list[dict[str, Any]] = []
    for entity in graph.entities.values():
        if entity.get("type") != "CareProcess":
            continue
        process_id = str(entity["id"])
        participants = graph.outgoing(process_id, "PARTICIPATED_BY")
        mdt.append(
            {
                "id": process_id,
                "label": graph.label(process_id),
                "departments": [
                    {
                        "id": str(fact.get("object")),
                        "label": graph.label(str(fact.get("object"))),
                        "evidence": _evidence_ids([fact], book),
                    }
                    for fact in participants
                ],
            }
        )

    review_statuses = sorted(
        {
            str((fact.get("provenance") or {}).get("review_status"))
            for fact in data.facts
            if fact.get("provenance")
        }
    )
    result = {
        "query": {
            "complaint": graph.label(complaint_id),
            "complaint_id": complaint_id,
            "findings": [graph.label(item) for item in finding_ids],
        },
        "conditions": conditions,
        "chief_complaint_tests": chief_tests,
        "triage": {
            "levels": triage_levels,
            "caveat": "分诊级别必须由分诊人员结合生命体征与动态变化判定；此处只列出与本次查询相关的候选指标，不自动定级。",
        },
        "mdt": mdt,
        "evidence": book.items,
        "review_statuses": review_statuses,
        "disclaimer": (
            "ED-ConsultKG M0 为研究用知识图谱，全部事实为 ai-draft，未经过临床专家审核；"
            "不得用于真实患者诊疗。"
        ),
    }
    return result


def render_text(result: dict[str, Any]) -> str:
    lines: list[str] = []
    query = result["query"]
    lines.append(f"# {query['complaint']} — ED-ConsultKG M0 检索结果")
    lines.append("")
    lines.append(f"> {result['disclaimer']}")
    if query.get("findings"):
        lines.append(f"> 已输入发现: {', '.join(query['findings'])}")
    lines.append("")

    lines.append("## 分诊候选指标")
    if not result["triage"]["levels"]:
        lines.append("- 当前图谱没有与该主诉匹配的分诊指标。")
    for level in result["triage"]["levels"]:
        area = "、".join(item["label"] for item in level.get("care_area") or []) or "未指定"
        parts = [level["label"]]
        if level.get("color") and level["color"] != "none":
            parts.append(f"颜色 {level['color']}")
        if level.get("response_time"):
            parts.append(f"响应 {level['response_time']}")
        parts.append(f"区域 {area}")
        lines.append(f"- {'；'.join(parts)}")
        for criterion in level["matched_criteria"]:
            kind = criterion.get("criterion_type") or "未标注"
            lines.append(
                f"  - 指标: {criterion['label']}（{kind}）"
                f" [{', '.join(criterion['evidence'])}]"
            )
    lines.append(f"> {result['triage']['caveat']}")
    lines.append("")

    if result.get("chief_complaint_tests"):
        lines.append("## 主诉级推荐检查")
        for item in result["chief_complaint_tests"]:
            qualifiers = item.get("qualifiers") or {}
            detail = _format_qualifiers(qualifiers)
            lines.append(f"- {item['label']}{detail} [{', '.join(item['evidence'])}]")
        lines.append("")

    lines.append("## 高危/相关鉴别")
    for condition in result["conditions"]:
        risk = condition.get("risk") or "未标注"
        lines.append(f"### {condition['label']}（风险: {risk}）")
        if condition.get("may_indicate", {}).get("evidence"):
            lines.append(
                "- 主诉关联: "
                f"{condition['may_indicate'].get('risk') or '未标注风险'}"
                f" [{', '.join(condition['may_indicate']['evidence'])}]"
            )
        has_structured = any(
            condition.get(key)
            for key in (
                "presentations",
                "red_flags",
                "differentiated_from",
                "distinguished_by",
                "recommended_tests",
                "treatments",
                "dispositions",
                "risk_factors",
                "consultations",
            )
        )
        if not has_structured:
            lines.append("- 当前图谱仅登记主诉关联；表现/检查/处置待 M1 用专科来源补充。")
        if condition.get("presentations"):
            lines.append(
                "- 典型表现: "
                + "；".join(
                    f"{item['label']} [{', '.join(item['evidence'])}]"
                    for item in condition["presentations"]
                )
            )
        if condition.get("red_flags"):
            lines.append(
                "- 红旗: "
                + "；".join(
                    f"{item['label']} [{', '.join(item['evidence'])}]"
                    for item in condition["red_flags"]
                )
            )
        if condition.get("differentiated_from"):
            lines.append(
                "- 需鉴别: "
                + "；".join(
                    f"{item['label']} [{', '.join(item['evidence'])}]"
                    for item in condition["differentiated_from"]
                )
            )
        if condition.get("distinguished_by"):
            lines.append(
                "- 鉴别要点: "
                + "；".join(
                    f"{item['label']} [{', '.join(item['evidence'])}]"
                    for item in condition["distinguished_by"]
                )
            )
        if condition.get("recommended_tests"):
            lines.append("- 推荐检查:")
            for item in condition["recommended_tests"]:
                detail = _format_qualifiers(item.get("qualifiers") or {})
                lines.append(f"  - {item['label']}{detail} [{', '.join(item['evidence'])}]")
        if condition.get("treatments"):
            lines.append(
                "- 治疗/干预: "
                + "；".join(
                    f"{item['label']} [{', '.join(item['evidence'])}]"
                    for item in condition["treatments"]
                )
            )
        if condition.get("dispositions"):
            lines.append(
                "- 处置/去向: "
                + "；".join(
                    f"{item['label']} [{', '.join(item['evidence'])}]"
                    for item in condition["dispositions"]
                )
            )
        if condition.get("risk_factors"):
            lines.append(
                "- 危险因素: "
                + "；".join(
                    f"{item['label']} [{', '.join(item['evidence'])}]"
                    for item in condition["risk_factors"]
                )
            )
        if condition.get("consultations"):
            lines.append(
                "- 会诊: "
                + "；".join(
                    f"{item['label']} [{', '.join(item['evidence'])}]"
                    for item in condition["consultations"]
                )
            )
        lines.append("")

    if result.get("mdt"):
        lines.append("## 多学科协作/会诊流程")
        for process in result["mdt"]:
            departments = "、".join(
                f"{item['label']} [{', '.join(item['evidence'])}]"
                for item in process["departments"]
            )
            lines.append(f"- {process['label']}: {departments or '未登记参与科室'}")
        lines.append("")

    lines.append("## 证据")
    for item in result["evidence"]:
        lines.append(
            f"- [{item['id']}] {item['source_id']} {item['locator']}: "
            f"“{item['quote']}”"
        )
    return "\n".join(lines) + "\n"


def _format_qualifiers(qualifiers: dict[str, Any]) -> str:
    if not qualifiers:
        return ""
    parts = [f"{key}={value}" for key, value in qualifiers.items() if value not in (None, "", [])]
    return f"（{'；'.join(parts)}）" if parts else ""
