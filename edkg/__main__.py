"""Command line entry point: python -m edkg {validate,stats,query}."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .loader import DataError, find_repo_root, load_repo
from .query import QueryError, query_complaint, render_text
from .stats import compute_stats, render_stats_text
from .validate import validate_repo


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="edkg", description="ED-ConsultKG M0 toolchain")
    parser.add_argument("--root", type=Path, default=None, help="repository root (default: auto-detect)")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate schema, sources, entities and facts")
    validate.add_argument("--strict", action="store_true", help="treat warnings as failures")
    validate.add_argument("--json", action="store_true", help="print the full JSON report")

    stats = sub.add_parser("stats", help="print graph statistics")
    stats.add_argument("--json", action="store_true", help="print JSON")

    query = sub.add_parser("query", help="query a chief complaint pathway")
    query.add_argument("--complaint", required=True, help="chief complaint label or id, e.g. 胸痛")
    query.add_argument("--finding", action="append", default=[], help="additional finding label or id")
    query.add_argument("--json", action="store_true", help="print JSON")
    return parser


def _load(args: argparse.Namespace):
    root = args.root or find_repo_root()
    return load_repo(root)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        data = _load(args)
    except DataError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.command == "validate":
        report = validate_repo(data, strict=args.strict)
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            for issue in report.issues:
                prefix = "ERROR" if issue.level == "error" else "WARN "
                location = f" [{issue.record_id}]" if issue.record_id else ""
                print(f"{prefix} {issue.code}{location}: {issue.message}")
            print(
                f"\n检查完成: {report.counts.get('entities', 0)} 实体, "
                f"{report.counts.get('facts', 0)} 事实, "
                f"{len(report.errors)} 错误, {len(report.warnings)} 警告"
            )
            print("结果:", "PASS" if report.ok(strict=args.strict) else "FAIL")
        return 0 if report.ok(strict=args.strict) else 1

    if args.command == "stats":
        stats = compute_stats(data)
        print(json.dumps(stats, ensure_ascii=False, indent=2) if args.json else render_stats_text(stats))
        return 0

    if args.command == "query":
        try:
            result = query_complaint(data, args.complaint, args.finding)
        except QueryError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_text(result))
        return 0

    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
