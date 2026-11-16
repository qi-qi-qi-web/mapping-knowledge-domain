# Schema v0.2（人读说明）

> 机器可读定义以 [`schema/edkg.schema.json`](../schema/edkg.schema.json) 为准；本文件解释设计意图与使用方式。

## 1. 三层结构

| 层 | 作用 | 实体 |
|---|---|---|
| 流程事件层 | 把“一次就诊”作为时序锚点，连接分诊/检查/鉴别/会诊/处置/转归 | `Visit`、`CareEvent` |
| 临床语义层 | 回答“这个主诉可能是什么、怎么查、怎么治” | `ChiefComplaint`、`Condition`、`Finding`、`Test`、`Intervention`、`RiskFactor`、`TriageScale`、`TriageLevel`、`TriageCriterion` |
| 组织资源层 | 回答“找谁、去哪、怎么转” | `Department`、`Role`、`CareProcess`、`CareArea`、`Disposition` |

当前阶段只实例化临床层、组织层与分诊量表；流程层只定义、不写患者实例，避免把真实就诊记录写进公开图谱。

## 2. 实体类型与 ID 前缀

| 类型 | 前缀 | 必填属性 | 说明 |
|---|---|---|---|
| `Visit` | `visit` | `label_zh` | 就诊事件；M0 不实例化 |
| `CareEvent` | `event` | `label_zh`, `stage` | 流程事件；M0 不实例化 |
| `ChiefComplaint` | `cc` | `label_zh` | 主诉，查询入口 |
| `Condition` | `cond` | `label_zh`, `condition_kind` | 疾病/综合征/症状复合体 |
| `Finding` | `find` | `label_zh`, `finding_kind` | 症状/体征/心电图/影像/实验室 |
| `Test` | `test` | `label_zh`, `test_kind` | 检查/检验/评分 |
| `Intervention` | `int` | `label_zh`, `intervention_kind` | 药物/操作/手术/支持 |
| `Department` | `dept` | `label_zh`, `department_kind` | 科室/院前 |
| `Role` | `role` | `label_zh`, `role_kind` | 会诊/分诊角色 |
| `CareProcess` | `proc` | `label_zh`, `process_kind` | 胸痛中心等协作流程 |
| `CareArea` | `area` | `label_zh`, `care_area_kind` | 复苏/抢救/优先/普通区 |
| `Disposition` | `disp` | `label_zh`, `disposition_kind` | 住院/ICU/转诊/离院 |
| `TriageScale` | `scale` | `label_zh`, `scale_id` | 分诊量表 |
| `TriageLevel` | `level` | `label_zh`, `scale_id`, `level` | 量表级别；颜色/时限/分区为来源事实，必须带 provenance |
| `TriageCriterion` | `crit` | `label_zh`, `criterion_kind` | 分诊判定标准（高危/意识/疼痛/资源/生命体征）；必须带 provenance |
| `RiskFactor` | `risk` | `label_zh` | 危险因素 |

ID 规则：`<prefix>.<slug>`，只允许小写字母、数字、下划线、点，例如 `cond.acs`、`find.bp_asymmetry`、`level.cn4.2`、`crit.esi.resources_0`。

## 3. 关系类型

| 关系 | domain → range | 主要 qualifiers | 当前 |
|---|---|---|---|
|---|---|---|---|
| `MAY_INDICATE` | `ChiefComplaint` → `Condition` | `risk` | 使用 |
| `PRESENTS_WITH` | `Condition` → `Finding` | `typicality` | 使用 |
| `HAS_RED_FLAG` | `Condition` → `Finding` | `note` | 使用 |
| `SUPPORTS` | `Finding` → `Condition` | `strength` | 使用 |
| `IS_A` | `Condition` → `Condition` | — | 预留（避免未核验层级） |
| `DIFFERENTIATED_FROM` | `Condition` → `Condition` | `note`；对称 | 使用 |
| `DISTINGUISHED_BY` | `Condition` → `Finding`/`Test` | `note` | 使用 |
| `RECOMMENDED_TEST` | `Condition`/`ChiefComplaint` → `Test` | `timing`, `priority`, `context` | 使用 |
| `TEST_YIELDS` | `Test` → `Finding` | — | 使用 |
| `TREATS` | `Intervention` → `Condition` | `context`, `urgency` | 使用 |
| `CONSULT` | `Condition` → `Department` | `urgency`, `consult_type` | 预留 |
| `TYPICAL_DISPOSITION` | `Condition` → `Disposition` | `context` | 使用 |
| `HAS_RISK_FACTOR` | `Condition` → `RiskFactor` | — | 使用 |
| `HAS_LEVEL` | `TriageScale` → `TriageLevel` | — | 使用 |
| `LEVEL_CRITERION` | `TriageLevel` → `Condition`/`Finding`/`TriageCriterion` | `criterion_type`（objective/artificial/algorithm，必填） | 使用 |
| `ASSIGNED_TO` | `TriageLevel` → `CareArea` | — | 使用 |
| `PARTICIPATED_BY` | `CareProcess` → `Department` | `note` | 使用 |
| `HAS_EVENT` | `Visit` → `CareEvent` | — | 预留 |
| `NEXT_EVENT` | `CareEvent` → `CareEvent` | — | 预留 |
| `USES_SCALE` | `Visit` → `TriageScale` | — | 预留 |
| `HAS_CHIEF_COMPLAINT` | `Visit` → `ChiefComplaint` | — | 预留 |

## 4. provenance

每条事实必须包含：

```json
{
  "source_id": "src.cn.chest_pain.2019",
  "locator": "§3.2.4 辅助检查",
  "quote": "所有胸痛患者在首次医疗接触后应在10 min内完成心电图检查",
  "confidence": 0.99,
  "assertion_type": "explicit",
  "review_status": "ai-draft",
  "extracted_by": "manual-curation",
  "extracted_at": "2026-10-29"
}
```

- `quote` 必须是原文连续片段；硬上限 300 字。
- `confidence` 是抽取置信度，不是临床概率。
- `assertion_type`：当前阶段只允许 `explicit`；`inferred` 需 `rationale`；`design` 不进入临床事实。
- `review_status`：`ai-draft` / `needs-review` / `human-reviewed` / `clinician-approved` / `deprecated`。

## 5. 约束

- 事实 ID 唯一；`(subject, predicate, object)` 唯一。
- 禁止自环；domain/range 必须匹配。
- 事实只能引用 `status=verified` 且 `used_in` 含 `mvp`/`m1` 的来源。
- 候选来源不得出现在任何事实中。
- `Condition.icd10` 仅当 `data/registry/icd10.json` 有对应 entry 时填写；entry 的 `code` 必须与实体一致。
- ICD-10 entry 必须引用 `src.who.icd10.2019`，`concept_url` 必须为 `https://icd.who.int/browse10/2019/en/GetConcept?ConceptId=<code>`，`quote` 为官方页面短引文；`no_single_code` 的 condition 不得填 `Condition.icd10`。
- 允许孤立实体（为后续扩展保留），但新增时应尽量挂接关系。

## 6. 当前覆盖（M1 进行中）

- **135 实体、192 事实**；7 份已核验来源：6 份进入事实（2 份中文共识 + AHRQ ESI v4 + 3 份 MSD），WHO ICD-10 仅用于编码映射。
- M0 基线：80 实体、116 事实；中国四级分诊 + 胸痛高危/中低危 + 胸痛中心。
- M1 增量：ESI v4 五级、12 个 `TriageCriterion`（立即救生、高危、意识、疼痛、危险区、资源 2+/1/0、4 个年龄分层危险区阈值）、17 条事实。
- M1-03：新增呼吸困难、腹痛、发热 3 个主诉，9 个 Condition、14 个 Finding、10 个 Test、1 个 Intervention；59 条事实；新 Condition 不填 ICD-10。
- ICD-10：`data/registry/icd10.json` 9 条 entry；8 个 `Condition.icd10`，ACS 为 `no_single_code`；每条有 `concept_url`、`locator`、`quote`、`match`、`source_id`。
- 分诊：中国四级 + ESI v4；两套量表分别建模，查询分组展示，**不互映射**。
- 危险区阈值：HR/RR 有文本引文；SaO2<92% 为 Figure 6-1 图像目视转录，裁剪图见 `docs/research/figures/esi_fig6_1_danger_zone.png`。
- 会诊：胸痛中心参与科室（院前/急诊/心内科）与转诊条件。
- Neo4j 投影（M1-04）：135 节点 / 192 关系；13 类节点标签、15 个谓词；`queries/` 下 10 个只读 Cypher 用例与 `expected.json` 离线夹具通过 JSONL 参考实现校验；不改 Schema，**未在真实 Neo4j 实例执行导入**。
- 未做：ICD-11/批量编码、真实 Neo4j 实例导入/性能验证、病种级专科会诊、流程事件实例。

## 7. 如何新增

1. 先确认来源已 `verified`；
2. 新增实体（唯一 ID、必填属性）；
3. 新增事实（domain/range 正确、qualifier 在 Schema 内、provenance 完整）；
4. 如需填 `Condition.icd10`，先在 `data/registry/icd10.json` 登记并保证 code/quote/URL 一致；
5. 数据变更后重跑 `python scripts/export_neo4j.py --out neo4j` 与 `python scripts/verify_neo4j_queries.py`；如用例结果有意变化，审查 diff 后用 `--write` 重生成 `expected.json`；
6. `python -m edkg validate --strict`；
7. `python scripts/audit_quotes.py`；
8. 更新 `DEVLOG.md`/`TODO.md`。
