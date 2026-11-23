# Neo4j 图谱导出

本目录是 `data/kg/entities.jsonl` 与 `data/kg/facts.jsonl` 的确定性 Neo4j 投影。源数据仍是 JSONL；本目录可由脚本重建，不应手工成为第二份知识源。

## 生成

```bash
python scripts/export_neo4j.py --out neo4j
```

输出：

| 路径 | 内容 |
|---|---|
| `neo4j/import/nodes_*.csv` | 13 类实体，共 135 行 |
| `neo4j/import/rels_*.csv` | 15 个谓词，共 188 行 |
| `neo4j/setup.cypher` | 唯一约束与检索索引 |
| `neo4j/import.cypher` | 28 条 `LOAD CSV WITH HEADERS` 导入语句 |

脚本会清空 `neo4j/import/*.csv` 后重写；两次导出内容字节一致。节点使用 `:Entity:<Type>` 双标签，关系使用静态谓词类型（如 `:MAY_INDICATE`），关系属性保留 `source_id`、`locator`、`quote`、`confidence`、`review_status`、`assertion_type`、`extracted_by`、`extracted_at` 与 qualifier。

## 导入本地 Neo4j

1. 启动一个本地 Neo4j 实例（本仓库未绑定具体版本），把 `neo4j/import/*.csv` 复制到该实例的 `import` 目录。
2. 在 Neo4j Browser 或 `cypher-shell` 执行：

   ```cypher
   :source neo4j/setup.cypher
   :source neo4j/import.cypher
   ```

   或分别粘贴两个文件的内容。
3. 确认计数：

   ```cypher
   MATCH (n) RETURN count(n) AS nodes;          // 期望 135
   MATCH ()-[r]->() RETURN count(r) AS rels;    // 期望 188
   ```

4. 用 [`queries/README.md`](../queries/README.md) 中的 10 个用例查询。

`setup.cypher` 只创建约束/索引，不清空数据；`import.cypher` 使用 `MERGE`，重复执行会按 `fact_id` 合并关系，但不会删除已存在的数据。若需从空白实例重来，请自行确认后执行（**破坏性操作，仅限本地测试**）：

```cypher
MATCH (n) DETACH DELETE n;
```

## 验证

```bash
python scripts/export_neo4j.py --out neo4j
python scripts/verify_neo4j_queries.py
```

`verify_neo4j_queries.py` 不连接 Neo4j；它检查 10 个 Cypher 文件与 `queries/cases.json`、`queries/expected.json` 一致，并用 `edkg.neo4j_cases` 的 Python 参考实现复核 JSONL 结果。

## 限制

- **未在真实 Neo4j 实例上执行导入**：开发环境无 Neo4j/`cypher-shell`，Docker daemon 不可用，`dist.neo4j.org` 返回 403；当前验收为静态检查 + JSONL 参考结果一致，不是运行时导入验收。
- 不依赖 APOC；`file:///...` 路径相对于 Neo4j 实例的 `import` 目录。
- 导出是只读投影；不会把 Neo4j 中的修改写回 JSONL。
- 全部事实仍是 `ai-draft`，未经临床审核；不得用于真实患者诊疗。
