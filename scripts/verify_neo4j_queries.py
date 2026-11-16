from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edkg.loader import find_repo_root, load_repo  # noqa: E402
from edkg.neo4j_cases import CASES, compute_all  # noqa: E402

_PARAM = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
_MUTATING = re.compile(r"\b(CREATE|MERGE|DELETE|SET|REMOVE|DROP|CALL)\b", re.IGNORECASE)


def _load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError(f"{path}: 'cases' must be a list")
    return cases


def _validate_case_files(root: Path, cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = [str(case.get("id")) for case in cases]
    if len(ids) != len(set(ids)):
        errors.append("duplicate case ids")
    if set(ids) != {str(case["id"]) for case in CASES}:
        errors.append("cases.json ids do not match edkg.neo4j_cases.CASES")
    for case in cases:
        case_id = str(case.get("id"))
        file_name = str(case.get("file"))
        if Path(file_name).name != file_name:
            errors.append(f"{case_id}: file must be a basename")
            continue
        path = root / "queries" / file_name
        if not path.is_file():
            errors.append(f"{case_id}: missing {path}")
            continue
        text = path.read_text(encoding="utf-8")
        params = set(_PARAM.findall(text))
        expected_params = set((case.get("params") or {}).keys())
        if params != expected_params:
            errors.append(
                f"{case_id}: Cypher params {sorted(params)} != case params {sorted(expected_params)}"
            )
        if "$" in text and not params:
            errors.append(f"{case_id}: unparsed parameter marker")
        if not re.search(r"\bMATCH\b", text, re.IGNORECASE):
            errors.append(f"{case_id}: no MATCH clause")
        if not re.search(r"\bRETURN\b", text, re.IGNORECASE):
            errors.append(f"{case_id}: no RETURN clause")
        if _MUTATING.search(text):
            errors.append(f"{case_id}: query must be read-only")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check the ten Cypher cases against offline reference results."
    )
    parser.add_argument("--root", type=Path, default=None, help="repository root")
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite queries/expected.json from the JSONL reference implementation",
    )
    args = parser.parse_args()

    root = args.root.resolve() if args.root else find_repo_root()
    cases_path = root / "queries" / "cases.json"
    cases = _load_cases(cases_path)
    errors = _validate_case_files(root, cases)

    data = load_repo(root)
    actual = compute_all(data)
    expected_path = root / "queries" / "expected.json"
    if args.write:
        expected_path.write_text(
            json.dumps(actual, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"wrote {expected_path}")
    else:
        if not expected_path.is_file():
            errors.append(f"missing {expected_path}; run with --write once")
        else:
            expected = json.loads(expected_path.read_text(encoding="utf-8"))
            if set(expected) != set(actual):
                errors.append("expected.json case ids do not match cases.json")
            for case_id in sorted(actual):
                if expected.get(case_id) != actual[case_id]:
                    errors.append(f"{case_id}: expected.json differs from JSONL reference")

    for case in cases:
        case_id = str(case.get("id"))
        print(f"{case_id}: {len(actual.get(case_id, []))} rows")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {len(cases)} Cypher cases, results match JSONL reference")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
