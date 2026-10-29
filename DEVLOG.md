# DEVLOG

> 追加式变更记录。新条目置于最上方；不改写历史，更正用新条目。
> 每条至少包含：日期、阶段、完成、决策、验证、commit、遗留/阻塞。

---

## 2026-10-29 | M0 仓库初始化与胸痛 MVP

### 背景

- 阅读并拆解 `docs/research/大规模急诊全流程会诊知识图谱研究报告.md`（170 行，8 张图）。
- 目标：先把“真实来源 + 可审计事实 + 可查询最小闭环 + 可持续治理”落地，而不是直接追求大规模。
- 计划经用户批准后执行；本条目记录实际完成情况。

### 完成

- [x] `Agent.md`：数据真实性五条、来源准入、事实生命周期、提交规范、DoD。
- [x] `schema/edkg.schema.json`：Schema v0.1（15 类实体、21 类关系、provenance/审核状态/约束）。
- [x] `data/registry/sources.json`：8 个来源登记（3 verified / 1 access_controlled / 4 candidate）。
- [x] `data/kg/entities.jsonl`：80 实体。
- [x] `data/kg/facts.jsonl`：116 事实，全部 `ai-draft`，provenance 100%。
- [x] `edkg/`：loader、validator、query、stats、CLI；零第三方依赖。
- [x] `scripts/verify_sources.py`、`scripts/audit_quotes.py`。
- [x] `tests/`：30 项单元测试（含 9 项负例）。
- [x] `docs/PLAN.md`、`docs/SCHEMA.md`、`docs/MVP.md`；原报告与图复制到 `docs/research/`。
- [x] `README.md`、`LICENSE`、`NOTICE.md`、`.gitignore`、`.gitattributes`、`pyproject.toml`、CI。

### 决策

| 编号 | 决策 | 理由 |
|---|---|---|
| D-001 | M0 只做胸痛一个主诉 | 来源完整、临床价值高、可在小规模验证闭环 |
| D-002 | 数据格式用 JSON/JSONL，零第三方依赖 | 环境无 PyYAML/pytest；可移植、CI 简单 |
| D-003 | M0 只用两份中文共识；ESI/ICD 留 M1 | 避免未核验映射/编码；先保证来源真实 |
| D-004 | 中国四级与 ESI 五级分别建模，不做映射 | 无可靠 crosswalk；防止错误分级 |
| D-005 | 全部事实 `ai-draft`，不声称临床验证 | 无临床专家参与；安全底线 |
| D-006 | 只存短引文+定位，不存全文/PDF | 版权限制；`NOTICE.md` 声明 |
| D-007 | 候选来源（MIMIC/DDXPlus/PrimeKG/ICD 等）只登记不使用 | 许可证/访问未核验；隔离风险 |
| D-008 | 事实必须过 `validate` 与 `audit_quotes` 双门 | 防 LLM/人工幻觉；可追溯 |
| D-009 | 代码 MIT；原创文档/数据 CC BY-NC 4.0 | 研究/非商业；第三方条款优先 |
| D-010 | 报告仅作设计输入，不搬其数字 | 报告引用未逐条核验 |
| D-011 | 优先 git；本机 git 传输不可用时用 GitHub API 提交 | 网络限制；API 提交仍是真实 commit |
| D-012 | M0 不实例化 Visit/CareEvent | 避免把患者记录写入公开图谱；流程层 M1 再做 |

### 验证（2026-10-29）

- `python -m edkg validate --strict`：**0 错误 / 0 警告**。
- `python -m unittest discover -s tests -v`：**30 项通过**。
- `python scripts/verify_sources.py`：3/3 开放来源 HTTP 200；AHRQ PDF 463,412 字节与登记一致。
- `python scripts/audit_quotes.py`：**116/116 引文命中**（HTML 去标签、归一空白后逐条比对）。
- `python -m edkg stats`：80 实体 / 116 事实 / provenance 100% / 重复三元组 0；仅引用 `src.cn.chest_pain.2019`（95 条）与 `src.cn.triage.2018`（21 条）。
- 查询：`python -m edkg query --complaint 胸痛` 可返回分诊候选指标（Ⅰ/Ⅱ/Ⅲ级）、高危鉴别、检查、治疗、处置、胸痛中心 MDT 与证据列表。

### 提交

- 仓库：https://github.com/qi-qi-qi-web/mapping-knowledge-domain
- 基线：`c730aa2f26c7b06afeeddd9898b312647dd7803a`（Initial commit，仅 README）
- 本次提交：**待远端提交后回填**（提交完成后以新 DEVLOG 条目记录 SHA；避免伪造 SHA）
- 方式：GitHub REST Git Data API（本机 `github.com` git 传输不可用）；凭据只在进程内读取，未落盘/未打印。

### 遗留/阻塞

- **临床审核未做**：全部 `ai-draft`；需要急诊/心内科专家双人盲评（TODO 阻塞项）。
- **ESI 五级未做**：AHRQ PDF 已登记，M1 抽取；不做四级/五级映射。
- **ICD 编码为空**：待 WHO 官方导出/许可核验。
- **低危病种结构化不足**：稳定性冠心病/GERD/肋软骨炎/神经官能症目前只有主诉关联。
- **病种级会诊未做**：M0 只有胸痛中心参与科室与转诊条件。
- **流程事件未实例化**：Visit/CareEvent 只有 Schema。
- **CI 状态**：workflow 已提交；是否运行以 GitHub Actions 为准，未运行前不写“CI 通过”。

### 下一步

- M1-01：ESI v4 五级标准抽取（独立量表，不做映射）。
- M1-02：WHO ICD-10 编码核验与填充。
- M1-03：呼吸困难/腹痛/发热 3 个主诉。
- M1-04：Neo4j/Cypher 导出 + 10 个查询用例。
- M1-05：20 条人工抽检 + 引文复核。
