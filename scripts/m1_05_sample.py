#!/usr/bin/env python3
"""Create the deterministic M1-05 review packet and blank review form."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from edkg.loader import load_repo  # noqa: E402
from edkg.quality import SEED, SAMPLE_SIZE, build_sample  # noqa: E402


def _write_bytes(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _packet_text(sample: dict) -> str:
    lines = [
        "# M1-05 双人盲评包",
        "",
        f"- 生成日期：{sample['generated_on']}",
        f"- 抽样总体：{sample['population_size']} 条事实",
        f"- 样本量：{sample['sample_size']}",
        f"- 随机种子：{sample['seed']}",
        f"- 抽样方法：{sample['method']}",
        "",
        "## 评审说明",
        "",
        "请两名评审者各自独立完成，不要互相讨论，也不要查看 `sample_manifest.json`。",
        "每条事实只判断三选一：`correct`（正确）、`partial`（部分正确）、`error`（错误）。",
        "依据页面给出的来源、定位和引文判断；不要用自身记忆补全引文未支持的内容。",
        "评审者 A 填 `review_a.csv`，评审者 B 填 `review_b.csv`；不要交换或覆盖文件。",
        "",
        "## 待评事实",
        "",
    ]
    for item in sample["items"]:
        statement = (
            f"{item['subject_label']}（`{item['subject']}`）"
            f" --{item['predicate_label']}--> "
            f"{item['object_label']}（`{item['object']}`）"
        )
        lines.extend(
            [
                f"### {item['sample_id']}",
                "",
                f"- 事实：{statement}",
                f"- 来源：{item['source_title']}（`{item['source_id']}`）",
                f"- 定位：{item['locator']}",
                f"- 引文：> {item['quote']}",
                "",
            ]
        )
        qualifiers = item.get("qualifiers") or {}
        if qualifiers:
            rendered = ", ".join(f"`{key}`={value}" for key, value in sorted(qualifiers.items()))
            lines.insert(-1, f"- 限定条件：{rendered}")
    lines.extend(
        [
            "## 判定规则",
            "",
            "- `correct`：主体、关系、客体和限定条件都得到引文支持，且没有明显临床歧义。",
            "- `partial`：核心关系对，但缺少重要限定，或引文只间接支持，或表述不够精确。",
            "- `error`：引文不支持该关系，主客体错误，或关系方向错误。",
            "",
            "本包只用于评审准备；在两名独立人类完成评审前，M1-05 不得标记为通过。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the M1-05 review sample")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    root = args.root.resolve()
    out_dir = (args.out or root / "evaluation" / "m1-05").resolve()
    for name in ("review_a.csv", "review_b.csv"):
        if (out_dir / name).exists():
            print(
                f"ERROR: {out_dir / name} already exists; "
                "refusing to overwrite a reviewer file",
                file=sys.stderr,
            )
            return 2

    data = load_repo(root)
    package = build_sample(data, size=SAMPLE_SIZE, seed=args.seed)
    sample = package["sample"]
    manifest = package["manifest"]
    out_dir.mkdir(parents=True, exist_ok=True)

    _write_bytes(out_dir / "sample.json", _json_text(sample))
    _write_bytes(out_dir / "sample_manifest.json", _json_text(manifest))
    _write_bytes(out_dir / "review_packet.md", _packet_text(sample))

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["sample_id", "verdict", "comment"])
    for item in sample["items"]:
        writer.writerow([item["sample_id"], "", ""])
    _write_bytes(out_dir / "review_template.csv", buffer.getvalue())

    print(f"sample: {out_dir / 'sample.json'}")
    print(f"manifest: {out_dir / 'sample_manifest.json'}")
    print(f"packet: {out_dir / 'review_packet.md'}")
    print(f"template: {out_dir / 'review_template.csv'}")
    print(
        f"facts: {sample['sample_size']} / {sample['population_size']}; "
        f"predicate strata: {len(sample['strata'])}; seed: {sample['seed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
