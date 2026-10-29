"""Check registered open sources over the network and print a report.

This script never edits the registry. A human (or agent) must review the
report and update `verification` deliberately.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edkg.loader import load_repo  # noqa: E402

USER_AGENT = "ED-ConsultKG-source-check/0.1 (research; contact repository owner)"


def fetch(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            content_type = response.headers.get("Content-Type", "")
            return {
                "ok": True,
                "http_status": response.status,
                "final_url": response.geturl(),
                "content_type": content_type,
                "content_length": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return {
            "ok": False,
            "http_status": getattr(exc, "code", None),
            "error": f"{type(exc).__name__}: {exc}",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="check open source URLs in the registry")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--include-candidates", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    data = load_repo(args.root or ROOT)
    results = []
    failures = 0
    for source in data.sources.get("sources", []):
        status = source.get("status")
        if status == "access_controlled":
            results.append({"id": source.get("id"), "skipped": "access_controlled"})
            continue
        if status == "candidate" and not args.include_candidates:
            results.append({"id": source.get("id"), "skipped": "candidate"})
            continue
        if not (source.get("url") or "").startswith(("http://", "https://")):
            results.append({"id": source.get("id"), "skipped": "no-url"})
            continue
        result = fetch(str(source["url"]))
        result["id"] = source.get("id")
        result["title"] = source.get("title")
        result["registered_content_length"] = (source.get("verification") or {}).get("content_length")
        results.append(result)
        if not result.get("ok"):
            failures += 1
        elif result.get("content_type", "").startswith("application/pdf"):
            expected = result.get("registered_content_length")
            if expected and expected != result.get("content_length"):
                result["warning"] = (
                    f"content_length changed: registry={expected}, fetched={result.get('content_length')}"
                )

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for result in results:
            if "skipped" in result:
                print(f"SKIP  {result['id']} ({result['skipped']})")
            elif result.get("ok"):
                print(
                    f"OK    {result['id']}  HTTP {result['http_status']}  "
                    f"{result['content_type'][:40]}  {result['content_length']} bytes"
                )
                if result.get("warning"):
                    print(f"      WARN {result['warning']}")
            else:
                print(f"FAIL  {result['id']}  {result.get('error')}")
    print(f"\nsources checked: {sum(1 for item in results if 'skipped' not in item)}, failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
