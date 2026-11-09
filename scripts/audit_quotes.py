"""Audit every fact quote against the live source text.

This is a release gate, not a CI step: it needs network access and source
availability. HTML source text is never written to disk. PDF extraction uses a
gitignored workspace scratch directory because sandboxed child processes may
not be able to write to the platform temp directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edkg.loader import load_repo  # noqa: E402
from edkg.normalize import quote_in_text, strip_html  # noqa: E402

USER_AGENT = "ED-ConsultKG-quote-audit/0.1 (research; contact repository owner)"


def fetch_text(url: str, context: ssl.SSLContext | None = None) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30, context=context) as response:
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
    # The platform temp directory can be restricted for child processes; use a
    # workspace-local, gitignored scratch directory (data/raw) and stable file
    # names. Do not delete the scratch directory from Python: some sandboxed
    # Windows setups deny directory removal even when file writes are allowed.
    scratch = ROOT / "data" / "raw" / "quote-audit"
    scratch.mkdir(parents=True, exist_ok=True)
    tag = hashlib.sha256(body).hexdigest()[:16]
    path = scratch / f"{tag}.pdf"
    output = scratch / f"{tag}.txt"
    error = scratch / f"{tag}.err"
    path.write_bytes(body)
    # Use -raw (reading order) and a file output so no pipe is involved.
    with error.open("w", encoding="utf-8") as error_file:
        completed = subprocess.run(
            [executable, "-raw", str(path), str(output)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=error_file,
        )
    if completed.returncode != 0:
        detail = error.read_text(encoding="utf-8", errors="replace").strip()
        raise RuntimeError(f"pdftotext failed: {detail}")
    return output.read_text(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="verify every fact and ICD-10 quote appears in its source")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--source", help="only audit facts citing this source id")
    parser.add_argument("--fact", help="only audit this fact id")
    parser.add_argument("--icd10", action="store_true", help="only audit ICD-10 registry quotes")
    parser.add_argument("--cafile", type=Path, default=None, help="PEM CA bundle for TLS verification")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.icd10 and (args.source or args.fact):
        parser.error("--icd10 cannot be combined with --source or --fact")

    context: ssl.SSLContext | None = None
    if args.cafile:
        try:
            context = ssl.create_default_context(cafile=str(args.cafile))
        except (OSError, ssl.SSLError) as exc:
            print(f"ERROR: cannot load CA bundle {args.cafile}: {exc}", file=sys.stderr)
            return 2

    data = load_repo(args.root or ROOT)
    sources = data.source_by_id
    cache: dict[str, str] = {}
    cache_error: dict[str, str] = {}
    failures: list[dict] = []
    checked = 0
    icd10_checked = 0

    def get_text(url: str) -> str | None:
        if url not in cache and url not in cache_error:
            try:
                cache[url] = fetch_text(url, context)
            except Exception as exc:  # noqa: BLE001 - report, do not crash the audit
                cache_error[url] = f"{type(exc).__name__}: {exc}"
        if url in cache_error:
            return None
        return cache.get(url)

    do_facts = not args.icd10
    do_icd10 = not (args.source or args.fact)

    if do_facts:
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
            url = str(source.get("url") or "")
            if not url:
                failures.append({"fact": fact_id, "source": source_id, "error": "source has no URL"})
                continue
            text = get_text(url)
            if text is None:
                failures.append(
                    {"fact": fact_id, "source": source_id, "error": cache_error.get(url, "fetch failed")}
                )
                continue
            quote = str(provenance.get("quote") or "")
            checked += 1
            if not quote_in_text(quote, text):
                failures.append(
                    {
                        "fact": fact_id,
                        "source": source_id,
                        "locator": provenance.get("locator"),
                        "quote": quote,
                        "error": "quote not found in fetched source text",
                    }
                )

    if do_icd10:
        registry = data.icd10 if isinstance(data.icd10, dict) else {}
        entries = registry.get("entries", [])
        if not entries:
            failures.append({"kind": "icd10", "error": "no ICD-10 registry entries"})
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                failures.append({"kind": "icd10", "entry": index, "error": "entry is not an object"})
                continue
            condition_id = str(entry.get("condition_id") or "")
            url = str(entry.get("concept_url") or "")
            quote = str(entry.get("quote") or "")
            if not url:
                failures.append(
                    {
                        "kind": "icd10",
                        "condition_id": condition_id,
                        "code": entry.get("code"),
                        "error": "entry has no concept_url",
                    }
                )
                continue
            text = get_text(url)
            if text is None:
                failures.append(
                    {
                        "kind": "icd10",
                        "condition_id": condition_id,
                        "code": entry.get("code"),
                        "url": url,
                        "error": cache_error.get(url, "fetch failed"),
                    }
                )
                continue
            icd10_checked += 1
            if not quote_in_text(quote, text):
                failures.append(
                    {
                        "kind": "icd10",
                        "condition_id": condition_id,
                        "code": entry.get("code"),
                        "source_id": entry.get("source_id"),
                        "url": url,
                        "locator": entry.get("locator"),
                        "quote": quote,
                        "error": "quote not found in fetched ICD-10 concept page",
                    }
                )

    fact_failures = [item for item in failures if item.get("kind") != "icd10"]
    icd10_failures = [item for item in failures if item.get("kind") == "icd10"]
    if args.json:
        print(
            json.dumps(
                {"checked": checked, "icd10_checked": icd10_checked, "failures": failures},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for failure in failures:
            label = (
                failure.get("fact")
                or failure.get("condition_id")
                or f"entry[{failure.get('entry')}]"
                or "?"
            )
            source = failure.get("source") or failure.get("source_id") or failure.get("url") or "-"
            print(f"FAIL {label} [{source}]: {failure.get('error')}")
            if failure.get("quote"):
                print(f"     quote={failure['quote']}")
        print(f"\nfacts checked: {checked}, failures: {len(fact_failures)}")
        print(f"ICD-10 quotes checked: {icd10_checked}, failures: {len(icd10_failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
