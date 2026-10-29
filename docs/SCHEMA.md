# Schema v0.1（人读说明）

> 机器可读定义以 [`schema/edkg.schema.json`](../schema/edkg.schema.json) 为准；本文件解释设计意图与使用方式。

## 1. 三层结构

| 层 | 作用 | 实体 |
|---|---|---|
| 流程事件层 | 把“一次就诊”作为时序锚点，连接分诊/检查/鉴别/会诊/处置/转归 | `Visit`、`CareEvent` |
| 临床语义层 | 回答“这个主诉可能是什么、怎么查、怎么治” | `ChiefComplaint`、`Condition`、`Finding`、`Test`、`Intervention`、`RiskFactor`、`TriageScale`、`TriageLevel` |
| 组织资源层 | 回答“找谁、去哪、怎么转” | `Department`、`Role`、`CareProcess`、`CareArea`、`Disposition` |

M0 只实例化临床层、组织层与分诊量表；流程层只定义、不写患者实例，避免把真实就诊记录写进公开图谱。

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
| `RiskFactor` | `risk` | `label_zh` | 危险因素 |

ID 规则：`<prefix>.<slug>`，只允许小写字母、数字、下划线、点，例如 `cond.acs`、`find.bp_asymmetry`、`level.cn4.2`。

## 3. 关系类型

| 关系 | domain → range | 主要 qualifiers | M0 |
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
| `LEVEL_CRITERION` | `TriageLevel` → `Condition`/`Finding` | `criterion_type`（必填） | 使用 |
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
- `assertion_type`：M0 只允许 `explicit`；`inferred` 需 `rationale`；`design` 不进入临床事实。
- `review_status`：`ai-draft` / `needs-review` / `human-reviewed` / `clinician-approved` / `deprecated`。

## 5. 约束

- 事实 ID 唯一；`(subject, predicate, object)` 唯一。
- 禁止自环；domain/range 必须匹配。
- 事实只能引用 `status=verified` 且 `used_in` 含 `mvp` 的来源。
- 候选来源不得出现在任何事实中。
- 允许孤立实体（为后续扩展保留），但新增时应尽量挂接关系。

## 6. M0 覆盖

- 80 实体、116 事实；只使用两份中文共识。
- 分诊：中国四级 + 非急症；颜色/响应时限/分区。
- 胸痛：ACS、急性心梗、AAD、APE、张力性气胸 + 4 个中低危示例。
- 会诊：胸痛中心参与科室（院前/急诊/心内科）与转诊条件。
- 未做：ESI 五级、ICD 编码、病种级专科会诊、流程事件实例。

## 7. 如何新增

1. 先确认来源已 `verified`；
2. 新增实体（唯一 ID、必填属性）；
3. 新增事实（domain/range 正确、qualifier 在 Schema 内、provenance 完整）；
4. `python -m edkg validate --strict`；
5. `python scripts/audit_quotes.py`；
6. 更新 `DEVLOG.md`/`TODO.md`。
