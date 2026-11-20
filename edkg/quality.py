"""M1-05 quality-evaluation helpers.

The sample is intentionally deterministic: one random fact per predicate plus
five additional facts from the largest predicate strata.  This is a coverage
sample, not a prevalence-weighted estimate of the whole graph.  Human reviewers
must work independently; this module never creates or fabricates review labels.
"""

from __future__ import annotations

import random
from collections import Counter
from datetime import date
from typing import Any

from .loader import RepoData

SAMPLE_SIZE = 20
SEED = 20261120
VERDICTS = ("correct", "partial", "error")
VERDICT_LABELS = {
    "correct": "正确",
    "partial": "部分正确",
    "error": "错误",
}
PREDICATE_LABELS = {
    "MAY_INDICATE": "可能提示",
    "PRESENTS_WITH": "表现为",
    "HAS_RED_FLAG": "危险信号",
    "RECOMMENDED_TEST": "推荐检查",
    "TREATS": "治疗",
    "HAS_RISK_FACTOR": "危险因素",
    "DIFFERENTIATED_FROM": "需鉴别",
    "DISTINGUISHED_BY": "鉴别依据",
    "TYPICAL_DISPOSITION": "典型去向",
    "HAS_LEVEL": "分诊级别",
    "LEVEL_CRITERION": "级别判定依据",
    "SUPPORTS": "支持",
    "TEST_YIELDS": "检查产出",
    "ASSIGNED_TO": "归属",
    "PARTICIPATED_BY": "参与角色",
}


def _sample_groups(facts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for fact in facts:
        predicate = str(fact["predicate"])
        groups.setdefault(predicate, []).append(fact)
    for rows in groups.values():
        rows.sort(key=lambda row: str(row["id"]))
    return groups


def build_sample(
    data: RepoData,
    *,
    size: int = SAMPLE_SIZE,
    seed: int = SEED,
) -> dict[str, Any]:
    """Build a reproducible, predicate-stratified 20-fact sample.

    Returns a package with ``sample`` (reviewer-facing content, no fact IDs or
    confidence) and ``manifest`` (sample_id -> fact_id mapping for auditing).
    """
    facts = list(data.facts)
    if size != SAMPLE_SIZE:
        raise ValueError(f"M1-05 requires exactly {SAMPLE_SIZE} facts, got {size}")
    if len(facts) < size:
        raise ValueError(f"not enough facts: {len(facts)} < {size}")

    groups = _sample_groups(facts)
    predicates = sorted(groups)
    if len(predicates) > size:
        raise ValueError("sample size is smaller than the number of predicate strata")

    rng = random.Random(seed)
    chosen: list[dict[str, Any]] = []
    chosen_ids: set[str] = set()

    # One fact from every predicate stratum, for coverage.
    for predicate in predicates:
        pick = rng.choice(groups[predicate])
        chosen.append(pick)
        chosen_ids.add(str(pick["id"]))

    # Fill the remaining slots from the largest strata.
    for predicate in sorted(predicates, key=lambda key: (-len(groups[key]), key)):
        if len(chosen) >= size:
            break
        remaining = [row for row in groups[predicate] if str(row["id"]) not in chosen_ids]
        if not remaining:
            continue
        pick = rng.choice(remaining)
        chosen.append(pick)
        chosen_ids.add(str(pick["id"]))

    if len(chosen) != size:
        remaining = [row for row in facts if str(row["id"]) not in chosen_ids]
        rng.shuffle(remaining)
        chosen.extend(remaining[: size - len(chosen)])
    if len(chosen) != size:
        raise ValueError(f"could not build a {size}-fact sample")

    rng.shuffle(chosen)
    entities = data.entity_by_id
    sources = data.source_by_id
    items: list[dict[str, Any]] = []
    manifest_items: list[dict[str, str]] = []
    for index, fact in enumerate(chosen, start=1):
        sample_id = f"M105-{index:02d}"
        subject = entities[str(fact["subject"])]
        obj = entities[str(fact["object"])]
        provenance = fact["provenance"]
        source_id = str(provenance["source_id"])
        source = sources[source_id]
        items.append(
            {
                "sample_id": sample_id,
                "subject": str(fact["subject"]),
                "subject_label": str(subject.get("label_zh", fact["subject"])),
                "predicate": str(fact["predicate"]),
                "predicate_label": PREDICATE_LABELS.get(str(fact["predicate"]), str(fact["predicate"])),
                "object": str(fact["object"]),
                "object_label": str(obj.get("label_zh", fact["object"])),
                "qualifiers": fact.get("qualifiers", {}),
                "source_id": source_id,
                "source_title": str(source.get("title", source_id)),
                "locator": str(provenance["locator"]),
                "quote": str(provenance["quote"]),
            }
        )
        manifest_items.append({"sample_id": sample_id, "fact_id": str(fact["id"])})

    strata = {
        predicate: {
            "population": len(groups[predicate]),
            "selected": sum(1 for item in items if item["predicate"] == predicate),
        }
        for predicate in predicates
    }
    sample = {
        "stage": "M1-05",
        "generated_on": date.today().isoformat(),
        "population_size": len(facts),
        "sample_size": size,
        "seed": seed,
        "method": (
            "predicate-stratified: one fact per predicate stratum, then five "
            "additional facts from the largest strata; within-stratum random "
            "selection; item order shuffled"
        ),
        "notes": (
            "Coverage-oriented sample; not a prevalence-weighted estimate. "
            "Reviewers must assess each item independently."
        ),
        "strata": strata,
        "items": items,
    }
    manifest = {
        "stage": "M1-05",
        "generated_on": sample["generated_on"],
        "seed": seed,
        "items": manifest_items,
    }
    return {"sample": sample, "manifest": manifest}


def normalize_reviews(
    rows: list[dict[str, str]],
    sample_ids: list[str],
) -> dict[str, str]:
    """Validate one reviewer's rows and return sample_id -> verdict."""
    if len(rows) != len(sample_ids):
        raise ValueError(
            f"review has {len(rows)} rows; expected {len(sample_ids)}"
        )
    expected = set(sample_ids)
    reviews: dict[str, str] = {}
    for row in rows:
        sample_id = (row.get("sample_id") or "").strip()
        verdict = (row.get("verdict") or "").strip().lower()
        if sample_id not in expected:
            raise ValueError(f"unknown sample_id: {sample_id!r}")
        if sample_id in reviews:
            raise ValueError(f"duplicate sample_id: {sample_id}")
        if verdict not in VERDICTS:
            raise ValueError(f"invalid verdict for {sample_id}: {verdict!r}")
        reviews[sample_id] = verdict
    missing = sorted(expected - set(reviews))
    if missing:
        raise ValueError(f"missing reviews: {', '.join(missing)}")
    return reviews


def _prf(
    reference: list[str],
    prediction: list[str],
    label: str,
) -> dict[str, float | int]:
    tp = sum(1 for ref, pred in zip(reference, prediction) if ref == label and pred == label)
    fp = sum(1 for ref, pred in zip(reference, prediction) if ref != label and pred == label)
    fn = sum(1 for ref, pred in zip(reference, prediction) if ref == label and pred != label)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def _cohen_kappa(a: list[str], b: list[str]) -> float:
    n = len(a)
    if n == 0:
        raise ValueError("cannot compute kappa on empty reviews")
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    count_a = Counter(a)
    count_b = Counter(b)
    expected = sum(
        (count_a[label] / n) * (count_b[label] / n) for label in VERDICTS
    )
    if expected == 1.0:
        return 1.0
    return round((observed - expected) / (1.0 - expected), 4)


def evaluate_reviews(
    sample: dict[str, Any],
    reviewer_a: list[dict[str, str]],
    reviewer_b: list[dict[str, str]],
) -> dict[str, Any]:
    """Compute descriptive accuracy, per-class agreement P/R/F1, and kappa.

    There is no external gold standard.  P/R/F1 are inter-reviewer agreement
    metrics (A as reference, B as prediction and the reverse), not claims about
    the whole graph.
    """
    items = sample.get("items", [])
    sample_ids = [str(item["sample_id"]) for item in items]
    if len(sample_ids) != SAMPLE_SIZE:
        raise ValueError(f"sample must contain {SAMPLE_SIZE} items")
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError("duplicate sample_id in sample")

    a = normalize_reviews(reviewer_a, sample_ids)
    b = normalize_reviews(reviewer_b, sample_ids)
    a_labels = [a[sample_id] for sample_id in sample_ids]
    b_labels = [b[sample_id] for sample_id in sample_ids]

    def summary(labels: list[str]) -> dict[str, Any]:
        counts = Counter(labels)
        correct = counts["correct"]
        partial = counts["partial"]
        return {
            "correct": correct,
            "partial": partial,
            "error": counts["error"],
            "strict_accuracy": round(correct / len(labels), 4),
            "lenient_accuracy": round((correct + 0.5 * partial) / len(labels), 4),
        }

    a_summary = summary(a_labels)
    b_summary = summary(b_labels)
    unanimous_correct = sum(1 for x, y in zip(a_labels, b_labels) if x == y == "correct")
    unanimous_wrong = sum(1 for x, y in zip(a_labels, b_labels) if x == y == "error")
    disagreements = sum(1 for x, y in zip(a_labels, b_labels) if x != y)

    inter_a = {label: _prf(a_labels, b_labels, label) for label in VERDICTS}
    inter_b = {label: _prf(b_labels, a_labels, label) for label in VERDICTS}

    def _macro_f1(prf: dict[str, dict[str, float | int]]) -> float:
        active = [
            label
            for label in VERDICTS
            if prf[label]["tp"] + prf[label]["fp"] + prf[label]["fn"] > 0
        ]
        if not active:
            return 0.0
        return round(sum(float(prf[label]["f1"]) for label in active) / len(active), 4)

    macro_a = _macro_f1(inter_a)
    macro_b = _macro_f1(inter_b)

    strict_min = min(a_summary["strict_accuracy"], b_summary["strict_accuracy"])
    unanimous_rate = round(unanimous_correct / len(sample_ids), 4)
    gate = strict_min >= 0.9 and unanimous_rate >= 0.9

    return {
        "stage": "M1-05",
        "sample_size": len(sample_ids),
        "reviewers": {
            "a": a_summary,
            "b": b_summary,
        },
        "agreement": {
            "observed": round((len(sample_ids) - disagreements) / len(sample_ids), 4),
            "kappa": _cohen_kappa(a_labels, b_labels),
            "unanimous_correct": unanimous_correct,
            "unanimous_error": unanimous_wrong,
            "disagreements": disagreements,
        },
        "inter_reviewer_prf": {
            "a_as_reference_b_as_prediction": {
                "per_class": inter_a,
                "macro_f1": macro_a,
            },
            "b_as_reference_a_as_prediction": {
                "per_class": inter_b,
                "macro_f1": macro_b,
            },
        },
        "gate": {
            "minimum_strict_accuracy": 0.9,
            "minimum_unanimous_correct_rate": 0.9,
            "strict_accuracy_min_of_two": strict_min,
            "unanimous_correct_rate": unanimous_rate,
            "passed": gate,
        },
        "notes": [
            "P/R/F1 are inter-reviewer agreement metrics; there is no external gold standard.",
            "A failed gate must be fixed by correcting data, not by changing the metrics.",
            "This report is only valid when both reviewers are independent humans.",
        ],
    }
