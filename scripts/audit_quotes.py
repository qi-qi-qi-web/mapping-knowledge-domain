"""Audit every fact quote against the live source text.

This is a release gate, not a CI step: it needs network access and source
availability. It never writes source text to disk (except a temporary PDF for
pdftotext, which is deleted immediately).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edkg.loader import load_repo  # noqa: E402
from edkg.normalize import quote_in_text, strip_html  # noqa: E402

USER_AGENT = "ED-ConsultKG-quote-audit/0.1 (research; contact repository owner)"


def fetch_text(source: dict) -> str:
    url = str(source.get("url"))
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        content_type = (response.headers.get("Content-Type") or "").lower()
        body = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return _pdf_to_text(body)
    text = body.decode(charset, errors="replace")
    if "html" in content_type or "<html" in text[:500].lower():
        return strip_html(text)
    return text


def _pdf_to_text(body: bytes) -> str:
    executable = shutil.which("pdftotext")
    if not executable:
        raise RuntimeError("pdftotext not found; cannot audit PDF quotes")
    with tempfile.TemporaryDirectory(prefix="edkg-audit-") as tmp:
        path = Path(tmp) / "source.pdf"
        path.write_bytes(body)
        completed = subprocess.run(
            [executable, "-layout", str(path), "-"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            raise RuntimeError(f"pdftotext failed: {completed.stderr.strip()}")
        return completed.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="verify every fact quote appears in its source")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--source", help="only audit facts citing this source id")
    parser.add_argument("--fact", help="only audit this fact id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    data = load_repo(args.root or ROOT)
    sources = data.source_by_id
    cache: dict[str, str] = {}
    cache_error: dict[str, str] = {}
    failures: list[dict] = []
    checked = 0

    for fact in data.facts:
        fact_id = str(fact.get("id"))
        provenance = fact.get("provenance") or {}
        source_id = str(provenance.get("source_id"))
        if args.source and source_id != args.source:
            continue
        if args.fact and fact_id != args.fact:
            continue
        source = sources.get(source_id)
        if not source:
            failures.append({"fact": fact_id, "source": source_id, "error": "source not registered"})
            continue
        if source_id not in cache and source_id not in cache_error:
            try:
                cache[source_id] = fetch_text(source)
            except Exception as exc:  # noqa: BLE001 - report, do not crash the audit
                cache_error[source_id] = f"{type(exc).__name__}: {exc}"
        if source_id in cache_error:
            failures.append({"fact": fact_id, "source": source_id, "error": cache_error[source_id]})
            continue
        quote = str(provenance.get("quote") or "")
        checked += 1
        if not quote_in_text(quote, cache[source_id]):
            failures.append(
                {
                    "fact": fact_id,
                    "source": source_id,
                    "locator": provenance.get("locator"),
                    "quote": quote,
                    "error": "quote not found in fetched source text",
                }
            )

    if args.json:
        print(json.dumps({"checked": checked, "failures": failures}, ensure_ascii=False, indent=2))
    else:
        for failure in failures:
            print(f"FAIL {failure.get('fact')} [{failure.get('source')}]: {failure.get('error')}")
            if failure.get("quote"):
                print(f"     quote={failure['quote']}")
        print(f"\nquotes checked: {checked}, failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
