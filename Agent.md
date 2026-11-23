# Agent.md — ED-ConsultKG 构建行为准则

> 本文件是后续任何人类贡献者、编码智能体或抽取智能体在本仓库工作时的**强制行为准则**。
> 它优先于临时偏好；与 `README.md`、`docs/PLAN.md` 冲突时，以本文件的数据真实性与安全条款为准。
> 当前版本：v0.2（M1 进行中，2026-11-04）。

---

## 0. 先读什么

按顺序读：

1. 本文件（规则）；
2. `docs/PLAN.md`（总体方案与路线图）；
3. `docs/SCHEMA.md`（实体、关系、provenance）；
4. `data/registry/sources.json`（哪些来源可用）；
5. `TODO.md`（当前优先级）；
6. `DEVLOG.md`（最近发生了什么）。

不要凭记忆或聊天记录直接改数据；以仓库文件为准。

---

## 1. 使命与非目标

### 1.1 使命

构建一个**流程感知、来源可审计、可增量扩展**的急诊全流程会诊知识图谱（ED-ConsultKG），为分诊、鉴别诊断、检查、多学科会诊、处置与转归提供可引用的结构化知识，支撑智能体诊断实验。

### 1.2 非目标

- 不是临床决策系统，不输出对真实患者的诊断/治疗结论。
- 不替代医生；不声称临床验证通过。
- 不在当前阶段追求“大规模”；先做可验证的最小闭环。
- 不把 LLM 记忆、二手综述、博客、未核验论文当作数据源。
- 不把真实病历/PHI 写入公开仓库。

---

## 2. 不可违反的红线

违反任一条，改动必须回滚：

1. **无来源不入库**：每条事实必须有 `provenance.source_id`、`locator`、`quote`；缺一即失败。
2. **无核验不引用**：事实只能引用 `status=verified` 且 `used_in` 含 `mvp`/`m1`（或当前阶段）的来源；`candidate` 绝不能出现在事实里。
3. **引文必须真实**：`quote` 必须是来源原文的连续片段，必须通过 `python scripts/audit_quotes.py`；不得用省略号拼接、改写或翻译后冒充原文。
4. **不得编造**：数据集、版本、URL/DOI、统计数字、专家意见、审核状态，一律不得凭空生成。找不到就写“未核验”，并放入 `candidate`。
5. **不得自批**：Agent 只能写 `ai-draft`/`needs-review`；`human-reviewed`/`clinician-approved` 只能由具名人类/临床专家设置。
6. **不得提交受限数据**：MIMIC、UMLS/SNOMED 全文、带版权指南全文/PDF、患者信息、密钥/token，一律不得进入仓库。
7. **不得伪造运行结果**：测试、CI、引文审计没跑就写“未运行”；失败就写失败。

---

## 3. 数据源准入与核验

### 3.1 来源等级（高 → 低）

1. 国家级学会指南/专家共识；
2. 官方手册/登记库（AHRQ、WHO、PhysioNet 等）；
3. 同行评议原始研究/系统综述；
4. 权威教科书；
5. 其他（默认不用于事实）。

当前阶段只接受前两类中已核验的来源。博客、百科、新闻、模型生成内容、报告中的二手数字，不作为事实来源。

### 3.2 来源登记

所有来源写入 `data/registry/sources.json`，至少包含：

```json
{
  "id": "src.<org>.<topic>.<year>",
  "type": "guideline_consensus | official_handbook | registry | dataset | software_repository | classification | paper",
  "title": "...",
  "publisher": "...",
  "year": 2019,
  "url": "https://...",
  "doi": "... or null",
  "access": "open | registration | credentialed | restricted",
  "license": "...",
  "redistribution": "quotes-only | full-allowed | no | unknown",
  "status": "verified | access_controlled | candidate | retired",
  "used_in": ["mvp", "m1", "evaluation"],
  "topics": ["..."],
  "verification": {
    "checked_at": "YYYY-MM-DD",
    "method": "http_get | api_get | manual_page_check",
    "http_status": 200,
    "content_type": "...",
    "content_length": 123,
    "notes": "..."
  }
}
```

### 3.3 状态规则

| 状态 | 可用于事实 | 规则 |
|---|---|---|
| `verified` | 是（且 `used_in` 含当前阶段） | 必须有可复核的核验记录 |
| `access_controlled` | 否 | 需 DUA/CITI 等；只用于未来评测，不进入公开图谱 |
| `candidate` | 否 | `used_in` 必须为空；许可证/版本未核验 |
| `retired` | 否 | 保留历史，不删除 |

### 3.4 核验动作

- 开放网页/PDF：运行 `python scripts/verify_sources.py`，记录 HTTP 状态、内容类型、长度；PDF 记录 SHA256。
- GitHub：用 REST API 确认仓库存在；许可证未确认时只能 `candidate`。
- 页面打不开/403：不得标 `verified`；写清失败原因，留在 `candidate`。
- 报告/论文里的“数据集清单”只是线索；必须回到原始登记页核验。

---

## 4. 事实模型与生命周期

### 4.1 事实格式

`data/kg/facts.jsonl`，一行一条：

```json
{
  "id": "fact.chest_pain.may_indicate.acs",
  "subject": "cc.chest_pain",
  "predicate": "MAY_INDICATE",
  "object": "cond.acs",
  "qualifiers": {"risk": "high"},
  "provenance": {
    "source_id": "src.cn.chest_pain.2019",
    "locator": "§1 急性胸痛救治现状",
    "quote": "不仅包括急性冠状动脉综合征（acute coronary syndrome，ACS）",
    "confidence": 0.99,
    "assertion_type": "explicit",
    "review_status": "ai-draft",
    "extracted_by": "manual-curation",
    "extracted_at": "2026-10-29"
  }
}
```

### 4.2 provenance 必填字段

`source_id`、`locator`、`quote`、`confidence`、`assertion_type`、`review_status`、`extracted_by`、`extracted_at`。可选：`rationale`、`conflict_group`、`valid_from`、`valid_to`、`notes`。

- `locator` 用章节号+标题（中文来源）或页码/表号（PDF）。
- `quote` 建议 ≤200 字、硬上限 300 字；只保留支撑该事实的最小片段。
- `confidence` 是**抽取置信度**，不是临床概率；精确引文默认 0.95–0.99。
- `assertion_type`：当前阶段只允许 `explicit`；`inferred` 必须写 `rationale` 并保持 `needs-review`；`design` 仅用于本体设计，不进入临床事实。
- `review_status`：`ai-draft` → `needs-review` → `human-reviewed` → `clinician-approved` → `deprecated`。

### 4.3 冲突与更新

- 两个来源矛盾：两条事实都保留，加同一个 `conflict_group`，标 `needs-review`；禁止静默覆盖。
- 指南更新：旧事实标 `deprecated`，写 `valid_to`；新增事实写 `valid_from`。
- 删除事实：优先废弃而非物理删除；确需删除时在 DEVLOG 说明原因。

---

## 5. Schema、ID 与查询规范

### 5.1 Schema

- 唯一机器可读定义：`schema/edkg.schema.json`。
- 新增实体/关系必须先改 Schema，再改数据；不得出现 Schema 外的类型。
- 关系必须有 `domain`/`range`；事实必须通过 domain/range 校验。
- 三套层：流程（Visit/CareEvent）、临床（Condition/Finding/Test/...）、组织（Department/CareProcess/CareArea/...）。

### 5.2 ID 规范

- 实体：`<prefix>.<slug>`，前缀与类型绑定，如 `cond.acs`、`find.bp_asymmetry`、`test.ecg_12lead`、`level.cn4.2`。
- 事实：`fact.<subject_short>.<predicate_lower>.<object_short>`，只允许小写字母、数字、下划线、点；必须唯一。
- 标签：`label_zh` 必填；`label_en`/`aliases` 可选。不要用中文做 ID。

### 5.3 分诊量表

- 中国四级（`scale.cn_4level_2018`）与 ESI 五级（`scale.esi_v4_2005`）**分别建模**。
- **禁止**编造两套量表的级别映射；如未来要做 crosswalk，必须单独立项、给出处、由临床专家审核。
- M0 填中国四级；M1 已填 ESI 五级（5 levels + 12 criteria，含 4 个年龄分层危险区阈值）；两套量表在查询输出中必须分组展示，禁止合并排序成单一等级。
- ESI 危险区阈值：HR/RR 有 `pdftotext -raw` 文本引文；SaO2<92% 为 Figure 6-1 图像目视转录（旋转文本未被文本抽取），裁剪图在 `docs/research/figures/esi_fig6_1_danger_zone.png`；新增阈值必须附来源/定位，不得凭记忆补数字。

### 5.4 编码

- `Condition.icd10` 只在 `data/registry/icd10.json` 有逐条核验记录时填写；每个 entry 必须有 `condition_id`、`code`、`title_en`、`concept_url`、`quote`、`match`、`source_id`。
- 只允许引用 `src.who.icd10.2019`（WHO ICD-10-WHO Version for 2019 / COVID-19 expanded）的官方 `GetConcept` 页；不得凭记忆写码，不得批量导入全文。
- `match` 区分 `exact` / `inclusion` / `broader` / `narrower` / `no_single_code`；ICD-10 没有 ACS 单一类目，`cond.acs` 必须为 `no_single_code` 且不填 `Condition.icd10`。
- 编码仅用于知识检索与来源追溯，不用于临床编码/计费；映射未经临床编码员审核。

### 5.5 查询

- `python -m edkg query --complaint 胸痛`（以及 `呼吸困难`、`腹痛`、`发热`）必须只返回图谱中有证据的条目，并附 evidence id。
- 分诊输出只列“候选指标”，**不得自动定级**；必须提示由分诊人员结合生命体征判定。
- 未收录主诉必须明确报错，不得生成无来源建议。

### 5.6 Neo4j/Cypher 导出

- `edkg/neo4j.py` 是 JSONL 的只读、确定性投影，生成 `neo4j/import/*.csv`、`setup.cypher`、`import.cypher`；源数据仍是 `data/kg/*.jsonl`。
- 不得手工修改 `neo4j/import/` 或 `queries/expected.json`；数据变化后重新运行 `python scripts/export_neo4j.py --out neo4j` 与 `python scripts/verify_neo4j_queries.py --write`，并审查 diff。
- `queries/*.cypher` 必须只读、带参数，且与 `queries/cases.json` 的 10 个用例对应；结果用 `edkg/neo4j_cases.py` 的 JSONL 参考实现和 `expected.json` 校验。
- 未在真实 Neo4j 实例执行前，文档只能写“离线一致性校验通过”，不得写“Neo4j 导入/运行通过”；不得声称已做性能或生产验证。

### 5.7 质量评估

- M1-05 只生成**给人类评审者使用的样本/表单/评估工具**；Agent 不得扮演评审者，不得用 AI 自查、两个 AI 子代理或模拟标签冒充“双人盲评”。
- 样本固定 20 条、固定 seed、按 predicate 分层；评审者看到的 `sample.json`/`review_packet.md` 不得含 `fact_id` 或置信度；`sample_manifest.json` 仅用于审计，评审期间不得展示。
- 只有两名独立人类都完成评审后，才能运行评估并报告正确率、P/R/F1、Kappa；在此之前 `TODO.md` 的 M1-05 只能是 `[!]`/阻塞，不得标 `[x]`。
- P/R/F1 是评审者间一致性指标，不是外部 gold standard 上的抽取性能；报告必须写明样本是覆盖导向、不能外推为全图准确率。
- gate 未过时修数据，不得改指标、改样本或伪造 `review_a.csv`/`review_b.csv`/`report.json`；不得把本地合成的测试标签当作评审结果。
- 任何评审结论都不能替代临床上线前的完整专家审核；全部事实仍保持 `ai-draft`，除非具名人类明确审核并记录。

---

## 6. 标准工作流

每次任务按以下顺序执行，不得跳步：

1. **读规则**：`Agent.md` → `TODO.md` → `docs/PLAN.md` 相关章节。
2. **查来源**：确认要用的来源已在 `sources.json` 且 `verified`；否则先做核验任务，不写事实。
3. **小步改**：一次只做一个主诉/一个病种/一类关系；先改 Schema（如需），再改数据。
4. **写引文**：从来源原文复制最短支撑句；定位到章节/表/页；立即写 `locator`。
5. **本地验证**：
   ```bash
   python -m edkg validate --strict
   python -m unittest discover -s tests -v
   python scripts/audit_quotes.py        # 有网络时；发布前必跑
   python scripts/verify_neo4j_queries.py
   python -m edkg stats
   ```
   M1-05 相关改动另跑 `python scripts/m1_05_sample.py`；只有两名独立人类完成后才运行 `python scripts/m1_05_evaluate.py`，没有真实评审时只验证工具，不产出质量结论。
6. **更新记录**：`DEVLOG.md` 写本次变更、决策、验证结果、commit；`TODO.md` 勾选/新增。
7. **提交**：Conventional Commits；一次提交一类事。
8. **远端验证**：确认远端 commit/tree/文件内容；CI 未跑就写“待运行”。

### 6.1 新增来源检查清单

- [ ] 原始页面/PDF 可访问，记录 HTTP 状态与长度；
- [ ] 许可与再分发方式写清；不能转载全文的只存短引文；
- [ ] 版本/年份明确；指南是否有更新版本；
- [ ] 加入 `sources.json`，状态先 `candidate`，核验后才 `verified`；
- [ ] 更新 `docs/PLAN.md` 的来源表（如适用）。

### 6.2 新增主诉/病种检查清单

- [ ] 主诉实体 + `MAY_INDICATE` 至少一个来源明确的病种；
- [ ] 高危病种有红旗/鉴别/检查/处置（有来源才写）；
- [ ] 每个病种至少 1 条检查或处置事实；
- [ ] 如涉及分诊，挂到明确的 `TriageLevel` 指标，不自行定级；
- [ ] 查询 CLI 能返回新主诉；测试覆盖；
- [ ] 无来源的部分写“待补充”，不得用常识补全。

---

## 7. 提交、发布与 GitHub 降级流程

### 7.1 提交规范

- 使用 Conventional Commits：`feat:`、`fix:`、`docs:`、`data:`、`test:`、`chore:`。
- 提交信息写“为什么”，不要只写“update”。
- 禁止 force push；禁止提交 `.env`、token、凭据、PHI、受限全文。
- 单人民研仓当前阶段允许直接提交 `main`；Schema 破坏性变更、批量数据导入须开分支/PR。

### 7.2 GitHub 传输降级

优先使用 `git`。若本机 `git` 传输不可用（网络/DNS/TLS 限制），允许使用 GitHub REST **Git Data API** 创建 commit 并更新 `main`：

- 通过 API 创建 blob → tree → commit → 更新 ref（`force:false`）；
- 凭据只从环境变量或本机凭据管理器读取，**不得写入文件、日志、提交信息或聊天输出**；
- 提交后必须用 API 复核 commit/tree/关键文件哈希，并把 SHA 写入 `DEVLOG.md`；
- 不得因为 git 不通就只改本地、谎称已提交。

### 7.3 CI

- `.github/workflows/ci.yml` 只做离线校验；
- 若 Actions 未启用/排队，DEVLOG 写“CI 未运行/待运行”，不得写“CI 通过”。

---

## 8. DEVLOG 与 TODO

### 8.1 DEVLOG

- 追加式；不改写历史条目；更正用新条目。
- 每条包含：日期、阶段、完成、决策（D-编号）、验证结果、commit、遗留/阻塞。
- 远端 commit SHA、测试/审计结果必须真实；没跑就写“未运行”。

### 8.2 TODO

- 按 M0/M1/M2/M3 分组；每项有 ID、验收标准、依赖、状态。
- 完成项勾选并链接 DEVLOG/commit；阻塞项写清阻塞原因与责任人（如有）。
- 不得把“计划”写成“完成”。

---

## 9. 安全、合规与许可

- **无 PHI**：不提交真实病历、姓名、病案号、就诊时间等可识别信息；示例病例必须标明合成。
- **MIMIC 等受限数据**：只在取得 DUA/CITI 后用于评测；不得进入公开图谱或测试夹具。
- **版权**：中文指南/共识只存短引文与定位；不提交全文/PDF；`NOTICE.md` 声明第三方权利。
- **许可**：代码 MIT；原创文档/数据 CC BY-NC 4.0；第三方内容以来源条款为准。
- **临床安全**：所有输出附免责声明；红旗/急危情况优先升级；不得延迟就医建议。

---

## 10. Definition of Done（每次改动）

- [ ] `python -m edkg validate --strict` 通过；
- [ ] `python -m unittest discover -s tests -v` 通过；
- [ ] 新增/修改事实的引文审计通过（联网时）；
- [ ] 没有候选来源被事实引用；
- [ ] 没有编造来源、数字、编码或审核状态；
- [ ] `DEVLOG.md` 与 `TODO.md` 已更新；
- [ ] 文档/Schema/查询与改动一致；
- [ ] 远端 commit 可验证；CI 状态如实记录；
- [ ] 明确写出仍未解决的问题。

---

## 11. 当前状态与下一步（M1 进行中，2026-11-23）

- 已完成：Schema v0.2、11 个来源登记（7 verified / 1 access_controlled / 3 candidate）、4 个主诉图谱 135 实体 / 188 事实、中国四级 + ESI v4 两套分诊量表、WHO ICD-10 9 条逐病种映射（8 个编码，ACS 无单一码）、校验器、scale-aware 查询 CLI、61 项测试、CI。
- M1 增量：ESI v4 五级、12 个 `TriageCriterion`（含 4 个年龄分层危险区阈值）、资源需求规则、危险区上调规则；WHO ICD-10 编码映射（`data/registry/icd10.json`，查询 JSON/文本展示）；M1-03 新增呼吸困难、腹痛、发热 3 个主诉（9 个 Condition、59 条事实，来源为 3 份 MSD 手册页面）；M1-04 新增 Neo4j CSV/Cypher 导出、10 个只读查询用例与离线一致性校验；M1-05 新增 20 条分层抽样、双人评审模板与离线评估器。
- 全部事实 `ai-draft`，引用 6 份事实来源（2 份中文共识 + AHRQ ESI v4 + 3 份 MSD）；WHO ICD-10 仅用于编码映射；**未做临床审核/临床编码员审核**。
- M1-04 的 135 节点/188 关系与 10 个查询用例已通过静态检查和 JSONL 参考结果比对；**本机无 Neo4j，未在真实实例执行导入**，不得表述为“Neo4j 运行验证通过”。
- M1-05 round 1 已运行但 gate 未通过（A 65%、B 85%、κ -0.0127）；评审 CSV 无姓名/角色，不能确认独立临床人员，只作内部历史。已按有引文依据的反馈删除 4 条关系/处置事实并修正 ESI 引文，事实数 192→188，round 2 样本已重抽；**两名独立人类评审仍未发生**，在 B-01 完成前没有正确率、Kappa 或质量通过结论，不得把 M1-05 标为完成。
- 未做：ICD-11/批量编码、真实 Neo4j 实例导入/性能验证、LLM 抽取、MIMIC/DDXPlus 评测、临床专家审核、双人质量评审、病种级专科会诊。
- 下一步见 `TODO.md` 的 M1；任何扩展先补来源核验与引文，再谈规模。
