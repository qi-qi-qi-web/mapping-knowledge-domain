# TODO

> 状态：`[ ]` 未开始｜`[~]` 进行中｜`[x]` 完成｜`[!]` 阻塞
> 规则见 [`Agent.md`](Agent.md)；方案见 [`docs/PLAN.md`](docs/PLAN.md)；历史见 [`DEVLOG.md`](DEVLOG.md)。

## M0：胸痛最小可行版本（2026-10-29）

- [x] **M0-01** Schema v0.1（15 类实体、21 类关系、provenance、审核状态）
  - 验收：`python -m edkg validate --strict` 0 错误。
- [x] **M0-02** 来源登记（3 verified / 1 access_controlled / 4 candidate）
  - 验收：事实只引用 verified；candidate `used_in` 为空。
- [x] **M0-03** 胸痛种子图谱（80 实体 / 116 事实）
  - 验收：≥4 个高危病种；全部事实带 source/locator/quote。
- [x] **M0-04** 中国四级分诊（级别/颜色/响应时限/分区/关键指标）
  - 验收：Ⅰ–Ⅳ + 非急症；查询可返回 Ⅰ/Ⅱ/Ⅲ 相关指标。
- [x] **M0-05** 零依赖工具链（validate/stats/query/CLI）
  - 验收：`python -m edkg query --complaint 胸痛` 可运行。
- [x] **M0-06** 引文审计与来源核验脚本
  - 验收：116/116 引文命中；3/3 开放来源 HTTP 200。
- [x] **M0-07** 30 项单元测试（含负例）
  - 验收：`python -m unittest discover -s tests -v` 通过。
- [x] **M0-08** 文档：Agent/PLAN/SCHEMA/MVP/README/DEVLOG/NOTICE/LICENSE
  - 验收：数据真实性、审核状态、边界写清。
- [x] **M0-09** 原报告与图复制到 `docs/research/`，加引用警示
  - 验收：报告不被当作已核验数据源。
- [x] **M0-10** 提交到远端仓库并验证
  - 验收：远端 commit/tree/关键文件可验证；DEVLOG 记录 SHA（第二次提交回填）。
  - 结果：main `d39f783e72e6d88ae584676ea505576a344a84c9`；42/42 blob 校验一致；CI run `40813253228` success。

## M1：第二层扩展（进行中）

- [x] **M1-01** ESI v4 五级标准抽取
  - 来源：`src.us.ahrq.esi.v4.2005`（已核验 PDF，公有领域）。
  - 已完成：`scale.esi_v4_2005` + 5 个级别 + 8 个 `TriageCriterion` + 13 条事实；查询支持 `--scale esi_v4_2005`，两套量表分组展示。
  - 验收：**不与四级映射**；`validate --strict` 通过。
- [x] **M1-01b** ESI 危险区生命体征年龄分层阈值
  - 已完成：4 个年龄段的 `crit.esi.danger_vitals_*` + 4 条 `LEVEL_CRITERION`；HR/RR 有 `pdftotext -raw` 文本引文；SaO2<92% 为 Figure 6-1 图像目视转录（旋转文本未被 pdftotext 抽取）。
  - 证据：Figure 6-1 裁剪图 `docs/research/figures/esi_fig6_1_danger_zone.png`（AHRQ 公有领域）。
  - 验收：每个年龄段有来源 + 图表定位；HR/RR 引文通过 `audit_quotes`；当前 133/133。
- [x] **M1-02** WHO ICD-10 编码核验与填充
  - 来源：WHO ICD-10-WHO Version for 2019 (COVID-19 expanded)，`src.who.icd10.2019` 已 verified/used_in m1；仅短引文，不批量复制。
  - 已完成：`data/registry/icd10.json` 9 条逐病种映射；8 个 `Condition.icd10`（I21.9/I71.0/I26.9/J93.0/I25.1/K21.9/M94.0/F48.9），ACS 为 `no_single_code`。
  - 验收：9/9 映射可回溯（每条含 `concept_url`、`quote`、`locator`、`match`、`source_id`）；`validate --strict` 0/0；ICD 9/9 引文命中；无凭记忆写码。
- [x] **M1-03** 新增 3 个主诉：呼吸困难、腹痛、发热
  - 已完成：3 个 `ChiefComplaint` + 9 个 Condition + 14 个 Finding + 10 个 Test + 1 个 Intervention；59 条事实；来源为 `src.msd.dyspnea.2025`、`src.msd.acute_abdominal_pain.2024`、`src.msd.fever.2026`（均 verified/m1、短引文）。
  - 覆盖：呼吸困难 4 high + 1 medium；腹痛 2 high + 1 medium；发热 3 high + 1 low；每个主诉 5–6 条主诉级检查。
  - 验收：查询 CLI 支持三主诉；每个病种有来源 + 引文；新增 4 项查询测试；总计 49 项测试；事实 192 条。
- [x] **M1-04** Neo4j/Cypher 导出 + 10 个查询用例
  - 已完成：`edkg/neo4j.py` 确定性导出 135 节点/192 关系/13 类节点/15 谓词、28 个 CSV；`neo4j/import.cypher` 无 APOC；`queries/01…10_*.cypher` 10 个只读用例 + `cases.json` + `expected.json`；`scripts/export_neo4j.py` / `scripts/verify_neo4j_queries.py`。
  - 验收：导出可重复；10 个用例与 JSONL 参考实现一致（9/11/6/2/6/11/12/8/20/6 行）；新增 8 项测试，总 57 项。
  - 限制：本机无 Neo4j/`cypher-shell`，Docker daemon 未启动，`dist.neo4j.org` 403；**未在真实 Neo4j 实例执行导入**，不得写成运行验证通过。
- [!] **M1-05** M1 质量评估（工具/样本已就绪；双人人类评审未完成，受 B-01 阻塞）
  - 已完成：`edkg/quality.py`、`scripts/m1_05_sample.py`、`scripts/m1_05_evaluate.py`；`evaluation/m1-05/` 的 20 条分层样本（seed `20261120`，覆盖 15 个谓词）、评审包、空白评分表、说明；新增 4 项测试，总 61 项。
  - 验收：两名独立人类完成“正确/部分/错误”评审后，运行评估器；正确率 ≥90%，报告 P/R/F1、Kappa。**当前没有评审结果，不得标 `[x]`，不得用 AI 自查或合成标签代替。**
  - 说明：P/R/F1 是评审者间一致性，不是外部 gold standard；样本为覆盖导向，不能外推全图。
- [ ] **M1-06** 病种级专科会诊
  - 只在指南明确写“应请 XX 科”时添加 `CONSULT`；不得推断。
  - 验收：每条会诊事实有引文；无来源的写 TODO。
- [ ] **M1-07** 低危病种结构化
  - 稳定性冠心病/GERD/肋软骨炎/神经官能症：补表现/检查/处置（有来源才写）。
  - 验收：查询输出不再只有“主诉关联”。

## M2：半自动抽取与评测

- [ ] **M2-01** LLM 候选抽取（Schema 约束 + 引文 span）
  - 候选只进 `needs-review`；quote 必须能回查；不得直接进静态层。
- [ ] **M2-02** HITL 审核队列
  - 逐条接受/修改/拒绝；记录审核人/时间/理由。
- [ ] **M2-03** 10 个主诉、30+ 高危病种
  - 规模目标 2k+ 实体 / 8k+ 事实；不以未核验数据凑数。
- [ ] **M2-04** L2 图谱任务评估
  - 链接预测 MRR/Hits@K；规则一致性；检索质量。
- [ ] **M2-05** 下游任务准备
  - DDXPlus 许可证核验；分诊/鉴别/会诊评测方案定稿。

## M3：大规模与论文

- [ ] **M3-01** 10k+ 实体 / 50k+ 关系（质量门优先）
- [ ] **M3-02** GraphRAG/路径检索实验（对照无检索 LLM、文档 RAG、通用图谱）
- [ ] **M3-03** MIMIC-IV-ED / KTAS / DDXPlus 评测（DUA/伦理合规）
- [ ] **M3-04** 资源轨/方法轨论文与开放数据发布

## 阻塞/等待

- [!] **B-01 临床专家审核**：需要急诊/心内科专家双人独立评审；M1-05 样本/评估工具已就绪，等待评审者；在此之前所有事实保持 `ai-draft`，M1-05 不得标 `[x]`。
- [!] **B-02 MIMIC-IV-ED**：CITI 培训 + PhysioNet DUA；未完成前不使用、不提交任何记录级数据。
- [!] **B-03 第三方许可证**：DDXPlus、TriageAgent、PrimeKG、CMeKG 的许可证/版本需逐个核验；未核验前保持 `candidate`。
- [x] **B-04 WHO ICD 编码**：已完成 9 条逐病种核验（8 个编码 + ACS 无单一码）；不做全量/批量导出；映射待临床编码员复核。
- [x] **B-05 GitHub git 传输**：本机不可用；已用 GitHub API 提交（见 DEVLOG）。其他环境优先 git。

## 维护性待办

- [ ] 每季度重跑 `scripts/verify_sources.py`，更新 `verification.checked_at`。
- [ ] 每次指南更新后检查旧事实，标 `deprecated`/`valid_to`。
- [ ] 补充 `docs/SCHEMA.md` 与 Schema 的自动一致性检查（M1）。
- [ ] 为 `edkg` 增加 `export --format cypher`（M1）。
- [ ] 请临床编码员复核 8 条 `Condition.icd10` 与 1 条 `no_single_code`（M1-02 遗留）。
