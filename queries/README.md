# Cypher 查询用例

本目录把 `data/kg/entities.jsonl` 与 `data/kg/facts.jsonl` 的图谱投影用于 10 个只读查询用例。源数据仍是 JSONL；Cypher 与 `expected.json` 都是可重复生成的投影，不反向修改源数据。

## 文件

| 文件 | 用途 |
|---|---|
| `01_*.cypher` … `10_*.cypher` | 10 个参数化、只读 Cypher 查询 |
| `cases.json` | 用例 id、文件与固定参数 |
| `expected.json` | 由 `edkg.neo4j_cases.compute_all()` 生成的期望结果（离线夹具） |

## 10 个用例

| # | 用例 | 参数 | 当前行数 | 内容 |
|---|---|---|---|---|
| 01 | 主诉鉴别 | `complaint_id=cc.chest_pain` | 9 | 主诉 → `MAY_INDICATE` 病种、危险度、ICD-10、来源/引文 |
| 02 | 高危病种 | 无 | 11 | 全部 `risk=high` 病种及其表现/红旗计数 |
| 03 | 主诉相关红旗 | `complaint_id=cc.chest_pain` | 6 | 主诉候选病种的 `HAS_RED_FLAG` |
| 04 | 病种检查 | `condition_id=cond.acute_mi` | 2 | 病种级 `RECOMMENDED_TEST` |
| 05 | 主诉检查 | `complaint_id=cc.dyspnea` | 6 | 主诉级 `RECOMMENDED_TEST` |
| 06 | 治疗选项 | `complaint_id=cc.chest_pain` | 11 | 候选病种的 `TREATS` |
| 07 | 分诊指标 | `scale_id=esi_v4_2005` | 12 | ESI 五级与 `LEVEL_CRITERION` |
| 08 | ICD-10 病种 | 无 | 8 | 有 `Condition.icd10` 的病种 |
| 09 | 病种证据 | `condition_id=cond.aad` | 20 | 病种相关的全部事实与 provenance |
| 10 | 来源覆盖 | 无 | 6 | 按 `source_id` 统计事实数 |

行数随数据增删变化；以 `python scripts/verify_neo4j_queries.py` 的当前输出为准。

## 本地验证（不需要 Neo4j）

```bash
python scripts/export_neo4j.py --out neo4j
python scripts/verify_neo4j_queries.py
```

- `export_neo4j.py` 生成 `neo4j/import/*.csv`、`neo4j/setup.cypher`、`neo4j/import.cypher`，并打印节点/关系/类型/谓词计数。
- `verify_neo4j_queries.py` 校验 10 个 `.cypher` 文件存在、参数与 `cases.json` 一致、查询只读，并把 Python 参考结果与 `expected.json` 比较；通过时输出 `OK: 10 Cypher cases, results match JSONL reference`。
- 若源数据有意变更，先检查 diff，再用 `python scripts/verify_neo4j_queries.py --write` 重生成 `expected.json`；不得手改夹具。

## 在 Neo4j 中执行（可选）

1. 启动一个本地 Neo4j 实例，把 `neo4j/import/*.csv` 复制到该实例的 `import` 目录。
2. 在 Neo4j Browser / `cypher-shell` 执行 `neo4j/setup.cypher`。
3. 执行 `neo4j/import.cypher`；脚本用 28 条 `LOAD CSV WITH HEADERS`，不依赖 APOC。
4. 打开任一 `*.cypher`，按 `cases.json` 设置参数，例如：

   ```cypher
   :param complaint_id => 'cc.chest_pain';
   ```

   然后执行查询。也可以在 `cypher-shell` 中用 `--param` 传参。

## 边界

- **未在真实 Neo4j 实例上执行**：当前开发环境无 Neo4j/`cypher-shell`，Docker daemon 未启动，`dist.neo4j.org` 返回 403；本目录的验收是静态查询检查 + JSONL 参考结果一致性，不是 Neo4j 运行时结果。
- 导出是单向投影；`neo4j/` 与 `expected.json` 不构成新的知识来源。
- 全部事实仍是 `ai-draft`，未经临床审核；查询结果不得用于真实患者诊疗。
- Cypher 只读；不要在查询用例中加入 `CREATE` / `MERGE` / `SET` / `DELETE`。
