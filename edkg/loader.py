"""Loaders for the ED-ConsultKG repository data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA_PATH = Path("schema") / "edkg.schema.json"
SOURCES_PATH = Path("data") / "registry" / "sources.json"
ENTITIES_PATH = Path("data") / "kg" / "entities.jsonl"
FACTS_PATH = Path("data") / "kg" / "facts.jsonl"


class DataError(ValueError):
    """Raised when a repository data file cannot be parsed."""


def find_repo_root(start: Path | None = None) -> Path:
    """Find the repository root by walking up to the schema file."""
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / SCHEMA_PATH).is_file():
            return candidate
    raise DataError(
        f"cannot find {SCHEMA_PATH} from {here}; run from the repository root "
        "or pass --root"
    )


def load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise DataError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise DataError(f"invalid JSON in {path}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise DataError(f"cannot read {path}: {exc}") from exc
    records: list[dict[str, Any]] = []
    for lineno, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DataError(
                f"invalid JSONL in {path}:{lineno}: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise DataError(f"{path}:{lineno}: each JSONL line must be an object")
        records.append(value)
    return records


@dataclass(frozen=True)
class RepoData:
    root: Path
    schema: dict[str, Any]
    sources: dict[str, Any]
    entities: list[dict[str, Any]]
    facts: list[dict[str, Any]]

    @property
    def source_by_id(self) -> dict[str, dict[str, Any]]:
        return {str(item.get("id")): item for item in self.sources.get("sources", [])}

    @property
    def entity_by_id(self) -> dict[str, dict[str, Any]]:
        return {str(item.get("id")): item for item in self.entities}


def load_repo(root: Path | None = None) -> RepoData:
    repo_root = Path(root).resolve() if root else find_repo_root()
    schema = load_json(repo_root / SCHEMA_PATH)
    sources = load_json(repo_root / SOURCES_PATH)
    entities = load_jsonl(repo_root / ENTITIES_PATH)
    facts = load_jsonl(repo_root / FACTS_PATH)
    return RepoData(repo_root, schema, sources, entities, facts)


def iter_source_records(data: RepoData) -> Iterable[dict[str, Any]]:
    return data.sources.get("sources", [])
