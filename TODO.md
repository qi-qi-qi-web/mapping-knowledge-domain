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

## M1：第二层扩展（下一步）

- [ ] **M1-01** ESI v4 五级标准抽取
  - 来源：`src.us.ahrq.esi.v4.2005`（已核验 PDF，公有领域）。
  - 范围：五级定义、算法、生命体征阈值、资源需求。
  - 验收：`scale.esi_v4_2005` + 5 个级别 + 指标事实；**不与四级映射**；引文审计 100%。
- [ ] **M1-02** WHO ICD-10 编码核验与填充
  - 来源：WHO 官方导出/许可；先核验版本与使用条款。
  - 范围：M0 的 9 个 Condition 至少 6 个有编码；编码必须可回溯。
  - 验收：`Condition.icd10` 填值；`sources.json` 新增 verified 来源；无凭记忆写码。
- [ ] **M1-03** 新增 3 个主诉：呼吸困难、腹痛、发热
  - 每个主诉 ≥2 个高危病种、≥1 个中低危、≥5 条检查/处置事实。
  - 验收：查询 CLI 支持；每个病种有来源 + 引文；测试覆盖。
- [ ] **M1-04** Neo4j/Cypher 导出 + 10 个查询用例
  - 导出 `entities`/`facts` 为 Cypher 或 CSV；提供 `queries/*.cypher`。
  - 验收：导入脚本可复现；10 个用例结果与 JSONL 查询一致。
- [ ] **M1-05** M1 质量评估
  - 20 条分层随机事实，双人盲评“正确/部分/错误”；报告 P/R/F1、Kappa。
  - 验收：正确率 ≥90%（达不到则修数据，不修指标）。
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

- [!] **B-01 临床专家审核**：需要急诊/心内科专家双人盲评；在此之前所有事实保持 `ai-draft`。
- [!] **B-02 MIMIC-IV-ED**：CITI 培训 + PhysioNet DUA；未完成前不使用、不提交任何记录级数据。
- [!] **B-03 第三方许可证**：DDXPlus、TriageAgent、PrimeKG、CMeKG 的许可证/版本需逐个核验；未核验前保持 `candidate`。
- [!] **B-04 WHO ICD 导出**：需确认官方导出方式与许可；M0 不给编码。
- [x] **B-05 GitHub git 传输**：本机不可用；已用 GitHub API 提交（见 DEVLOG）。其他环境优先 git。

## 维护性待办

- [ ] 每季度重跑 `scripts/verify_sources.py`，更新 `verification.checked_at`。
- [ ] 每次指南更新后检查旧事实，标 `deprecated`/`valid_to`。
- [ ] 补充 `docs/SCHEMA.md` 与 Schema 的自动一致性检查（M1）。
- [ ] 为 `edkg` 增加 `export --format cypher`（M1）。
