#!/usr/bin/env python3
"""Evaluate two independent M1-05 human review files."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from edkg.quality import VERDICT_LABELS, VERDICTS, evaluate_reviews  # noqa: E402


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing header")
        if "sample_id" not in reader.fieldnames or "verdict" not in reader.fieldnames:
            raise ValueError(f"{path}: needs sample_id and verdict columns")
        return [dict(row) for row in reader]


def _print_report(report: dict) -> None:
    print("M1-05 质量评估")
    print(f"样本量: {report['sample_size']}")
    for key, label in (("a", "评审 A"), ("b", "评审 B")):
        row = report["reviewers"][key]
        print(
            f"{label}: correct={row['correct']}, partial={row['partial']}, "
            f"error={row['error']}, strict={row['strict_accuracy']:.2%}, "
            f"lenient={row['lenient_accuracy']:.2%}"
        )
    agreement = report["agreement"]
    print(
        f"一致性: observed={agreement['observed']:.2%}, "
        f"kappa={agreement['kappa']:.4f}, disagreements={agreement['disagreements']}"
    )
    for key, label in (
        ("a_as_reference_b_as_prediction", "A 为参考 / B 为预测"),
        ("b_as_reference_a_as_prediction", "B 为参考 / A 为预测"),
    ):
        block = report["inter_reviewer_prf"][key]
        print(f"P/R/F1（{label}）:")
        for verdict in VERDICTS:
            row = block["per_class"][verdict]
            print(
                f"  {VERDICT_LABELS[verdict]}: P={row['precision']:.2%}, "
                f"R={row['recall']:.2%}, F1={row['f1']:.2%}"
            )
        print(f"  macro-F1={block['macro_f1']:.2%}")
    gate = report["gate"]
    print(
        f"Gate: strict_min={gate['strict_accuracy_min_of_two']:.2%}, "
        f"unanimous_correct={gate['unanimous_correct_rate']:.2%}, "
        f"passed={'yes' if gate['passed'] else 'no'}"
    )
    for note in report["notes"]:
        print(f"  - {note}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Evaluate M1-05 human reviews")
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument(
        "--sample",
        type=Path,
        default=None,
        help="sample.json (default: evaluation/m1-05/sample.json)",
    )
    parser.add_argument(
        "--a",
        type=Path,
        default=None,
        help="reviewer A CSV (default: evaluation/m1-05/review_a.csv)",
    )
    parser.add_argument(
        "--b",
        type=Path,
        default=None,
        help="reviewer B CSV (default: evaluation/m1-05/review_b.csv)",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = args.root.resolve() / "evaluation" / "m1-05"
    sample_path = (args.sample or out_dir / "sample.json").resolve()
    a_path = (args.a or out_dir / "review_a.csv").resolve()
    b_path = (args.b or out_dir / "review_b.csv").resolve()

    try:
        if not sample_path.exists():
            raise ValueError(f"sample not found: {sample_path}")
        if not a_path.exists():
            raise ValueError(f"reviewer A file not found: {a_path}")
        if not b_path.exists():
            raise ValueError(f"reviewer B file not found: {b_path}")
        if a_path.read_bytes() == b_path.read_bytes():
            raise ValueError(
                "reviewer A and B files are byte-identical; use two independent reviews"
            )
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
        report = evaluate_reviews(sample, _read_csv(a_path), _read_csv(b_path))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_report(report)
    return 0 if report["gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
