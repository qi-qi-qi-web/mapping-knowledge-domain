from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edkg.loader import find_repo_root, load_repo  # noqa: E402
from edkg.neo4j import write_export  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the ED knowledge graph for Neo4j.")
    parser.add_argument("--root", type=Path, default=None, help="repository root")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("neo4j"),
        help="output directory (default: neo4j)",
    )
    args = parser.parse_args()

    root = args.root.resolve() if args.root else find_repo_root()
    data = load_repo(root)
    out = args.out if args.out.is_absolute() else root / args.out
    counts = write_export(data, out)
    print(
        f"nodes: {counts['nodes']}, relationships: {counts['relationships']}, "
        f"node_types: {counts['node_types']}, predicates: {counts['predicates']}"
    )
    print(f"output: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
