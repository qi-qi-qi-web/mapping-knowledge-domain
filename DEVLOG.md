# DEVLOG

> 追加式变更记录。新条目置于最上方；不改写历史，更正用新条目。
> 每条至少包含：日期、阶段、完成、决策、验证、commit、遗留/阻塞。

---

## 2026-11-13 | M1-03：呼吸困难、腹痛、发热 3 个主诉

### 背景

- M1-02 完成后为 98 实体 / 133 事实；只有胸痛 1 个主诉，呼吸困难、腹痛、发热尚无主诉实体。
- 原三份事实来源不足以支撑腹痛/发热的病种、检查、处置；必须新增真实、可访问、可逐条引文审计的来源，不能凭记忆写。
- 目标：3 个主诉各 ≥2 个高危病种、≥1 个中低危、≥5 条检查/处置事实；查询 CLI 与测试覆盖。

### 完成

- [x] 新增 3 份 MSD 诊疗手册专业版中文来源：`src.msd.dyspnea.2025`、`src.msd.acute_abdominal_pain.2024`、`src.msd.fever.2026`；均 verified、`used_in=["m1"]`、HTTP 200、quotes-only、记录版本号与评审日期。
- [x] 新增 3 个 `ChiefComplaint`：`cc.dyspnea`、`cc.abdominal_pain`、`cc.fever`。
- [x] 新增 9 个 Condition：急性心力衰竭、肺炎、哮喘急性发作、急性胰腺炎、急性阑尾炎、急性胆囊炎、脓毒症、脑膜炎、病毒性上呼吸道感染。
- [x] 新增 14 个 Finding、10 个 Test、1 个 Intervention（`int.antibiotics`）；59 条事实，全部 `ai-draft` / `explicit` / `manual-curation`。
- [x] 查询支持三主诉；每个主诉有 5–6 条主诉级检查；新增 4 项查询测试，总计 49 项。
- [x] 修复 `edkg/query.py`：中国四级胸痛指标只对 `cc.chest_pain` 生效，避免腹痛/发热继承胸痛分诊标准。
- [x] 同步 README/Agent/PLAN/SCHEMA/MVP/NOTICE/TODO 的计数、来源与 M1-03 边界。

### 决策

| 编号 | 决策 | 理由 |
|---|---|---|
| D-027 | 用 3 份 MSD 诊疗手册专业版中文页作为 M1-03 来源 | 真实可访问、有版本/评审日期、页面内可逐条定位；比指南全文更适合按病种摘取 |
| D-028 | 新 Condition 不填 ICD-10 | ICD-10 映射只对 M1-02 的 9 个胸痛病种逐条核验；新病种未做编码核验，不能顺手补码 |
| D-029 | 每主诉只写来源明确的主诉级检查/处置，不推断专科会诊 | 保持“无来源不写”；病种级会诊留给 M1-06 |
| D-030 | 中国四级胸痛指标按 `complaint_id == "cc.chest_pain"` 限定 | 原逻辑把所有含“胸痛”标签的 Finding 加入所有查询，导致腹痛/发热误显示胸痛分诊标准 |
| D-031 | MSD 仅短引文 + 章节定位，quotes-only，不批量复制 | 页面为版权内容；只保留支撑事实的短引文与来源链接 |

### 验证

- `python -m edkg validate --strict`：**PASS，135 实体 / 192 事实 / 9 条 ICD-10，0 错误 0 警告**。
- `python -m unittest discover -s tests -v`：**49 项通过**。
- `python scripts/audit_quotes.py --cafile <临时公共 CA bundle>`：**事实 192/192 + ICD-10 9/9 命中**。
- `python scripts/verify_sources.py --cafile <临时公共 CA bundle>`：**7/7 开放来源 HTTP 200**（2 中文共识、AHRQ ESI、WHO、3 份 MSD）；1 access_controlled + 3 candidate 跳过。
- `python -m edkg stats`：provenance 100%、重复三元组 0、来源 7 verified / 1 access_controlled / 3 candidate。
- 查询：呼吸困难 4 high + 1 medium、腹痛 2 high + 1 medium、发热 3 high + 1 low；各主诉 5–6 条主诉级检查。

### 提交

- 基线 main：`bb8c989f93c20219275720b176bf41065a0054c1`（M1-02）。
- 提交信息：`M1-03: add dyspnea, abdominal pain, and fever complaints`。
- 未 force push；提交 SHA 以 GitHub main 历史为准；网络失败时本条将补充“未能推送”。

### 遗留/阻塞

- **未临床审核**：全部事实 `ai-draft`，包括新增 9 个病种。
- **新病种无 ICD-10**：未做编码核验，不声称已编码。
- **分诊未扩展**：新主诉没有新增中国四级/ESI 病种级指标，只保留通用算法指标；中国四级指标对非胸痛主诉为空。
- **专科会诊未做**：M1-03 不写病种级 `CONSULT`。
- **MSD 版权**：仅短引文，不转载全文；正式再分发前需再次核对使用条款。

### 下一步

- M1-04：Neo4j/Cypher 导出 + 10 个查询用例。
- 维护项：临床编码员复核 8 条 ICD 映射；新增病种后续补编码需先核验来源。

---

## 2026-11-09 | M1-02：WHO ICD-10 编码核验与填充

### 背景

- M1-01b 完成后为 98 实体 / 133 事实；9 个 Condition 均未填 `icd10`。
- `src.who.icd10.2019` 原为 candidate，需先核验版本、访问与许可，不能凭记忆写码。
- 目标：9 个病种逐条映射，至少 6 个有编码；每条能回溯到 WHO 官方页面。

### 完成

- [x] WHO 来源核验：`src.who.icd10.2019` 改为 verified、`used_in=["m1"]`、HTTP 200、21,878 bytes；版本头为 *ICD-10-WHO Version for 2019 (COVID-19 expanded)*。
- [x] 新增 `data/registry/icd10.json`：9 条 entry，每条含 `condition_id`、`code`、`title_en`、`concept_url`、`locator`、`quote`、`match`、`source_id`、`checked_at`、`note_zh`。
- [x] 8 个 `Condition.icd10`：I21.9、I71.0、I26.9、J93.0、I25.1、K21.9、M94.0、F48.9；`cond.acs` 不填单一码。
- [x] Schema 增加 `icd10_match_type` 枚举与 `min_coded_conditions=6`；版本仍为 0.2.0。
- [x] 校验器新增 `_validate_icd10`：跨 registry/实体/来源检查 code 一致、格式、URL、quote、match、来源状态与最少编码数。
- [x] 查询 JSON/文本展示编码、匹配类型、来源与“不用于临床编码/计费”提示；stats 输出 9/8/1。
- [x] 引文审计支持 per-entry `concept_url`、`--icd10`、`--cafile`；来源核验支持 `--cafile`。
- [x] 新增 9 项测试（validate 6 + query 2 + stats 1），共 45 项。
- [x] 同步 README/Agent/PLAN/SCHEMA/MVP/NOTICE/TODO。

### 决策

| 编号 | 决策 | 理由 |
|---|---|---|
| D-022 | 使用独立 `data/registry/icd10.json`，`Condition.icd10` 仍为 string | 不改图谱计数与关系模型；逐条来源/引文/URL 放在 registry，实体只保留查询值 |
| D-023 | 9 个病种全部登记；8 个编码，ACS 为 `no_single_code` | ICD-10 无 ACS 单一类目，I24.9 不等同 ACS；避免强行合并 |
| D-024 | `match` 区分 exact/inclusion/broader/narrower/no_single_code | 明确部分匹配与反证，不把“可用码”说成“精确等价” |
| D-025 | WHO 只用于编码 registry，不进入事实；仅短引文，不批量复制 | 遵守 WHO 条款，保持“事实只引三份来源”的既有边界 |
| D-026 | 审计按 `concept_url` 逐条回查；本机用临时 CA bundle `--cafile` | WHO 链的 GoDaddy 根不在本机 Windows 根库；不关闭证书校验、不提交证书 |

### 验证

- `python -m edkg validate --strict`：**PASS，98 实体 / 133 事实 / 9 条 ICD-10，0 错误 0 警告**。
- `python -m unittest discover -s tests -v`：**45 项通过**。
- `python scripts/audit_quotes.py --cafile <临时公共 CA bundle>`：**事实 133/133 + ICD-10 9/9 命中**。
- `python scripts/verify_sources.py --cafile <临时公共 CA bundle>`：**4/4 开放来源 HTTP 200**（含 WHO）；其余 1 access_controlled + 3 candidate 按策略跳过。
- `python -m edkg stats`：provenance 100%、重复三元组 0、来源 4 verified / 1 access_controlled / 3 candidate。
- 查询：`--scale esi_v4_2005` 下 ACS 显示“无单一编码”，其余 8 个病种显示 code + 匹配类型。

### 提交

- 基线 main：`80e9cbc59e000033e60006d264102bb0fd630f93`（M1-01b）。
- 提交信息：`M1-02: add verified WHO ICD-10 mappings for chest pain conditions`。
- 未 force push；推送结果与远端校验以 GitHub main 历史为准；若网络失败，本条将补充“未能推送”。

### 遗留/阻塞

- **未经临床编码员审核**：8 条映射与 1 条 `no_single_code` 均为研究性登记。
- **不用于临床编码/计费**：仅用于知识检索与来源追溯。
- **不做 ICD-11/批量编码**：只覆盖当前 9 个胸痛病种。
- **本机 TLS 根不完整**：WHO 链根不在 Windows 根库；审计使用临时 `--cafile`，证书未提交、未关闭校验。

### 下一步

- M1-03：呼吸困难/腹痛/发热 3 个主诉。
- 临床编码员复核 8 条映射（维护性 TODO）。

---

## 2026-11-04 | M1-01b：ESI 危险区年龄分层阈值

### 背景

- M1-01 已入库 ESI 五级、8 条算法指标与资源规则；剩余 Figure 6-1 的年龄分层 HR/RR/SaO2 阈值。
- 目标：按 `<3月 / 3月–3岁 / 3–8岁 />8岁` 四层补阈值，保留来源与图表定位，不凭记忆补数字。

### 完成

- [x] 新增 4 个 `TriageCriterion`：`crit.esi.danger_vitals_infant`、`crit.esi.danger_vitals_3m_3y`、`crit.esi.danger_vitals_3_8y`、`crit.esi.danger_vitals_over8y`。
- [x] 新增 4 条 `level.esi.2 LEVEL_CRITERION` 事实（criterion_type=algorithm）。
- [x] 阈值：HR >180/>160/>140/>100；RR >50/>40/>30/>20；SaO2<92%。
- [x] 新增 Figure 6-1 裁剪图 `docs/research/figures/esi_fig6_1_danger_zone.png`（AHRQ 公有领域，SHA256 `a2463956…`）。
- [x] 更新 TODO/Agent/PLAN/SCHEMA/MVP/README/NOTICE 的计数与说明。
- [x] 新增 1 项测试（年龄分层阈值），共 36 项。

### 决策

| 编号 | 决策 | 理由 |
|---|---|---|
| D-019 | 用 4 个年龄分层 `TriageCriterion`，不把阈值写成自由文本 | 便于查询/审计；每个年龄段独立来源与定位 |
| D-020 | HR/RR 引文取 `pdftotext -raw` 的图表行；SaO2<92% 用 Figure 6-1 图像目视转录 | SaO2 是旋转文本，pdftotext 未完整抽取；不伪造文本引文，改用可复核裁剪图 |
| D-021 | 保留通用 `crit.esi.danger_zone_vitals` 作为上调规则，年龄分层指标作为具体阈值 | 规则与阈值分离；查询同时显示 |

### 验证

- `python -m edkg validate --strict`：**0 错误 / 0 警告**（98 实体 / 133 事实）。
- `python -m unittest discover -s tests -v`：**36 项通过**。
- `python scripts/audit_quotes.py`：**133/133 引文命中**；4 条年龄分层 HR/RR 引文均命中。
- `python -m edkg stats`：provenance 100%、重复三元组 0。
- 查询：`--scale esi_v4_2005` 的 ESI 2级下显示 4 个年龄分层危险区指标 + 通用上调规则。

### 提交

- 基线 main：`bad6ca08e5f26963d218c0faeafd54b543f5a953`（M1-01）。
- M1-01b 提交 SHA：以 GitHub main 历史为准（DEVLOG 不记录自身 SHA，避免递归）。
- 方式：GitHub REST Git Data API；未 force push；凭据不落盘。
- CI：推送后由 Actions 运行，结果以 run 页面为准。

### 遗留/阻塞

- **未临床审核**：全部 `ai-draft`；不能用于真实患者。
- **SaO2 证据形态**：为图像目视转录，不是 `pdftotext` 文本引文；已在 TODO/Agent/NOTICE 说明，裁剪图可复核。
- **ICD 编码/新主诉/Neo4j/专科会诊**：仍未做。
- **流程事件**：Visit/CareEvent 仍只有 Schema。

### 下一步

- M1-02：WHO ICD-10 官方导出/许可核验与编码填充。
- M1-03：呼吸困难/腹痛/发热。
- M1-04：Neo4j/Cypher 导出。

---

## 2026-11-01 | M1-01：ESI v4 五级分诊标准

### 背景

- M0 已完成胸痛种子图谱与中国四级分诊（80 实体 / 116 事实）。
- 按 `TODO.md` 的 M1-01，使用已登记的 AHRQ ESI v4 公有领域 PDF，增加第二套独立分诊量表。
- 目标：五级定义 + 判定指标 + 资源规则；**不与中国四级做映射**。

### 完成

- [x] Schema v0.2：新增 `TriageCriterion` 实体；`level_value` 增加 `5`；`criterion_type` 增加 `algorithm`；`LEVEL_CRITERION` range 扩展到 `TriageCriterion`。
- [x] 来源：`src.us.ahrq.esi.v4.2005` 更新核验记录（2026-11-01，PDF SHA256 `6cdf2d2c…`），`used_in=m1`。
- [x] 实体：`scale.esi_v4_2005`、`level.esi.1`–`level.esi.5`、8 个 `crit.esi.*`，共 14 个。
- [x] 事实：5 条 `HAS_LEVEL` + 8 条 `LEVEL_CRITERION`，共 13 条。
- [x] 查询：`--scale cn_4level_2018|esi_v4_2005`；默认按量表分组展示；两套量表不互映射。
- [x] 引文审计：PDF 改为 `pdftotext -raw`，工作区 scratch 文件，129/129 命中。
- [x] 测试：35 项（新增 ESI 量表/过滤/未知量表/分组测试）。
- [x] 文档：Agent/PLAN/SCHEMA/MVP/README/TODO/NOTICE 同步。

### 决策

| 编号 | 决策 | 理由 |
|---|---|---|
| D-013 | 新增 `TriageCriterion` 实体，不把资源需求硬塞成 Finding | ESI 的“≥2 项资源”是算法规则，不是症状/体征 |
| D-014 | 中国四级与 ESI 五级分别建模、查询分组，不生成 crosswalk | 无可靠映射；混用会导致错误分级 |
| D-015 | ESI 事实使用 `used_in=m1`，Schema 允许 `mvp/m1` | 保持 M0/M1 来源使用边界 |
| D-016 | 查询对 ESI 显示全部算法指标，对中国四级只显示与当前主诉相关的指标 | ESI 1/2 规则对任意患者都适用；中国四级指标是具体病种/发现 |
| D-017 | PDF 审计用 `-raw` + 工作区 scratch，不删除 scratch 目录 | 多栏 PDF 的 reading order 更稳定；沙箱对临时目录删除有限制 |
| D-018 | 年龄分层危险区阈值暂不填数字 | PDF 表格列在文本抽取中不完整；不凭记忆补数字，列 M1-01b |

### 验证

- `python -m edkg validate --strict`：**0 错误 / 0 警告**。
- `python -m unittest discover -s tests -v`：**35 项通过**。
- `python scripts/audit_quotes.py`：**129/129 引文命中**（含 AHRQ PDF）。
- `python -m edkg stats`：94 实体 / 129 事实 / provenance 100% / 重复三元组 0。
- 查询：`python -m edkg query --complaint 胸痛 --scale esi_v4_2005` 返回 5 个级别与 8 条算法指标；中国四级查询仍正常。
- 来源核验：`python scripts/verify_sources.py` **3/3 HTTP 200**（含 AHRQ PDF 463,412 bytes）。

### 提交

- 基线 main：`795d9319c4fd3e4c4375064bfe239f348549263e`（M0 最新）。
- M1 提交 SHA：以 GitHub main 历史为准（DEVLOG 不记录自身 SHA，避免递归）。
- 方式：GitHub REST Git Data API；未 force push；凭据不落盘。
- CI：推送后由 Actions 运行，结果以 run 页面为准。

### 遗留/阻塞

- **未临床审核**：全部 `ai-draft`；不能用于真实患者。
- **M1-01b**：ESI 年龄分层危险区 HR/RR/SpO2 阈值待核对 Figure 6-1 原表；当前只有“超过危险区考虑上调 ESI 2”的规则，没有具体阈值。
- **ICD 编码**：仍全部留空。
- **病种级会诊/低危结构化**：仍未做。
- **流程事件**：Visit/CareEvent 仍只有 Schema。

### 下一步

- M1-01b：核对 ESI 危险区阈值表，逐年龄段补事实。
- M1-02：WHO ICD-10 编码核验。
- M1-03：呼吸困难/腹痛/发热。
- M1-04：Neo4j/Cypher 导出。

---

## 2026-10-29 | M0 远端提交回填与验证

### 提交

- 远端 M0 commit：`d39f783e72e6d88ae584676ea505576a344a84c9`
- 回填提交：`36180f972b4641e59a028c6e4527049a6f5d3343`；CI run `40813380321`，`completed / success`
- main 的最新 SHA 以 GitHub 仓库为准；DEVLOG 不记录自身提交的 SHA，避免递归
- URL：https://github.com/qi-qi-qi-web/mapping-knowledge-domain/commit/d39f783e72e6d88ae584676ea505576a344a84c9
- tree：`493ec920265213d68f6c83095836e0b4ba7ea0bf`
- 文件：42 个；42/42 本地 Git blob SHA 与远端 main tree 一致。
- CI：GitHub Actions run `40813253228`，`completed / success`
  （https://github.com/qi-qi-qi-web/mapping-knowledge-domain/actions/runs/40813253228）。
- 方式：GitHub REST Git Data API；未 force push；未改写历史。

### 发布故障与处理

- 首次 ref 更新被远端拒绝，定位到 `.gitignore` 中与证书（PEM）和 Python 字节码字符类相关的两条通配模式触发内容校验。
- 处理：字节码改为逐后缀显式忽略（pyc/pyo/pyd），移除证书通配；实际忽略策略不变（仓库无证书/字节码文件）。
- 失败尝试产生的 dangling commit 未被任何 ref 引用，不影响 main；最终 `PATCH main` 成功。
- 结论记入 `Agent.md` 的提交降级流程：遇到远端内容校验拒绝时，先定位最小触发内容，再重试；不得用 force push 绕过。

### 验证

- 提交前：`validate --strict` 0 错误 0 警告；30 项测试通过；116/116 引文命中；3/3 开放来源 HTTP 200。
- 提交后：M0 commit 的 42/42 blob SHA 与 main tree 逐一比对一致；回填提交后，4 个文档 blob 再次校验一致；CI 两次均通过。
- 提交后未修改代码/数据；本条目只回填 SHA、CI 与故障处理。

### 下一步

- 按 `TODO.md` 的 M1 执行：ESI 五级、WHO ICD-10、3 个新主诉、Neo4j 导出、20 条人工抽检。
- 在临床专家介入前，所有事实继续保持 `ai-draft`。

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
- 本次提交：`d39f783e72e6d88ae584676ea505576a344a84c9`（见上方回填条目）
- 方式：GitHub REST Git Data API（本机 `github.com` git 传输不可用）；凭据只在进程内读取，未落盘/未打印。

### 遗留/阻塞

- **临床审核未做**：全部 `ai-draft`；需要急诊/心内科专家双人盲评（TODO 阻塞项）。
- **ESI 五级未做**：AHRQ PDF 已登记，M1 抽取；不做四级/五级映射。
- **ICD 编码为空**：待 WHO 官方导出/许可核验。
- **低危病种结构化不足**：稳定性冠心病/GERD/肋软骨炎/神经官能症目前只有主诉关联。
- **病种级会诊未做**：M0 只有胸痛中心参与科室与转诊条件。
- **流程事件未实例化**：Visit/CareEvent 只有 Schema。
- **CI 状态**：已通过（Actions run 40813253228，见上方回填条目）。

### 下一步

- M1-01：ESI v4 五级标准抽取（独立量表，不做映射）。
- M1-02：WHO ICD-10 编码核验与填充。
- M1-03：呼吸困难/腹痛/发热 3 个主诉。
- M1-04：Neo4j/Cypher 导出 + 10 个查询用例。
- M1-05：20 条人工抽检 + 引文复核。
