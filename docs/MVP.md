# 胸痛 MVP（M0 + M1 ESI）

> 状态：研究用最小可行版本 + ESI v4 增量；所有事实 `ai-draft`，未经临床专家审核，不得用于真实患者诊疗。

## 1. 为什么选胸痛

- 急诊最常见、时间依赖性最强的主诉之一；
- 高危鉴别（ACS/AAD/APE/张力性气胸）明确，适合验证“流程感知 + 鉴别”；
- 已核验的三份来源（两份中文共识 + AHRQ ESI v4）提供了分诊、危险分层、检查、治疗、MDT 与五级分诊的完整段落，可在 M0/M1 做端到端闭环。

## 2. 范围

| 维度 | 内容 |
|---|---|
| 主诉 | 胸痛 |
| 高危病种 | 急性冠脉综合征、急性心肌梗死、急性主动脉夹层、急性肺栓塞、张力性气胸 |
| 中低危示例 | 稳定性冠心病、胃食管反流病、急性肋软骨炎、神经官能症 |
| 分诊 | 中国四级标准（Ⅰ–Ⅳ + 非急症）+ ESI v4 五级；两套独立，不互映射 |
| 检查 | 心电图、hs-cTn、CK-MB、肌红蛋白、D-二聚体、BNP、血气、胸片、CTA、床旁超声、Wells、PESI |
| 治疗 | PCI、溶栓、抗血小板、抗凝、β受体阻滞剂、镇痛、胸腔穿刺减压、胸腔闭式引流 |
| 组织 | 胸痛中心（院前急救/急诊科/心内科）；不具备 PCI/大血管手术/引流能力时转诊 |
| 规模 | 94 实体、129 事实（M0 80/116 + M1 ESI 14/13） |

## 3. 来源与定位

| 来源 | 使用的章节 |
|---|---|
| `src.cn.chest_pain.2019` | §1 病因；§3.1 分诊策略；§3.2 危险分层（病史/症状/查体/辅助检查）；§3.3.3 非心源性鉴别；§4.1–4.5 检查；§5.1–5.4 治疗；§6 胸痛中心 |
| `src.cn.triage.2018` | §3/表 1 四级标准与响应时限；§4/表 2 分区；§3.1 级别定义 |
| `src.us.ahrq.esi.v4.2005` | ESI 五级定义；Decision Point A/B；资源需求；危险区规则（Figure 3-1/6-1） |

未使用：ICD 编码（M1-02）、MIMIC/DDXPlus（后评测）、CMeKG/PrimeKG（候选）。
未完成：ESI 年龄分层危险区阈值（PDF 表格列抽取不完整，M1-01b）。

## 4. 查询

```bash
# 文本
python -m edkg query --complaint 胸痛

# JSON（供智能体/前端）
python -m edkg query --complaint 胸痛 --json

# 附加发现（可选）
python -m edkg query --complaint 胸痛 --finding 类似心脏因素的胸痛

# 只看法定量表之一
python -m edkg query --complaint 胸痛 --scale cn_4level_2018
python -m edkg query --complaint 胸痛 --scale esi_v4_2005
```

### 输出包含

1. **分诊候选指标**：中国四级（Ⅰ/Ⅱ/Ⅲ级相关指标）与 ESI 五级（1–5 级算法指标）分组展示，附颜色/响应时限/区域；明确提示“不自动定级、不互映射”。
2. **主诉级检查**：心电图 10 min 内、胸痛三联 CTA。
3. **高危鉴别**：每个病种的表现、红旗、需鉴别疾病、鉴别要点、推荐检查、治疗、处置、危险因素。
4. **胸痛中心 MDT**：参与科室与来源。
5. **证据列表**：`[evN] source_id locator: “原文引文”`。

## 5. 示例输出（节选）

```text
## 分诊候选指标（两套量表独立，不互映射）
### 中国急诊预检分诊四级标准（2018）
- Ⅱ级 急重；颜色 橙色；响应 10 min；区域 抢救区
  - 指标: 类似心脏因素的胸痛（artificial） [ev63]
  - 指标: 急性心肌梗死（artificial） [ev64]
  - 指标: 急性肺栓塞（artificial） [ev64]
  - 指标: 急性主动脉夹层（artificial） [ev64]
### 急诊严重度指数（ESI）第4版
- ESI 1级 立即抢救；响应 immediate
  - 指标: 需要立即救生干预（algorithm/acuity） [ev66]
- ESI 2级 高危/不能等待；响应 generally within 10 minutes of arrival
  - 指标: 高危情况（可能迅速恶化或需时间敏感治疗）（algorithm/acuity） [ev67]
  - 指标: 新发意识混乱/嗜睡/定向障碍（algorithm/mental_status） [ev68]
  - 指标: 严重疼痛/痛苦（≥7/10）（algorithm/pain） [ev69]
  - 指标: 危险区生命体征（考虑上调至 ESI 2）（algorithm/vital_sign） [ev70]
- ESI 3级 需≥2项资源
  - 指标: 预计需要≥2项资源（algorithm/resource） [ev71]
...
```

（实际输出以 `python -m edkg query --complaint 胸痛` 为准；evidence id 会随数据增删变化。）

## 6. 质量门

- `python -m edkg validate --strict`：0 错误 0 警告；
- `python -m unittest discover -s tests -v`：35 项通过；
- `python scripts/audit_quotes.py`：129/129 引文命中（2026-11-01）；
- `python scripts/verify_sources.py`：3/3 开放来源 HTTP 200；
- 事实引用 3 个 `verified` 来源；0 重复三元组；provenance 100%。

## 7. 已知限制

- **未临床审核**：全部 `ai-draft`；不能用于真实患者。
- **两套量表不互映射**：中国四级与 ESI 五级分别建模；未做、也不做未经专家论证的交叉映射。
- **ESI 危险区阈值未完成**：年龄分层 HR/RR/SpO2 表在 PDF 文本抽取中列不完整，未凭记忆补数字（M1-01b）。
- **无 ICD 编码**：`Condition.icd10` 全部留空。
- **会诊较薄**：只写胸痛中心参与科室与转诊条件，未写病种级专科会诊。
- **低危病种结构化不足**：稳定性冠心病/胃食管反流病/肋软骨炎/神经官能症目前只有“主诉可能提示”一条事实，表现/检查待补。
- **流程层未实例化**：Visit/CareEvent 只有 Schema，没有患者事件。
- **规模小**：94/129，不是“大规模”；规模目标见 `docs/PLAN.md`。

## 8. 下一步

见 `TODO.md` 的 M1：M1-01b 危险区阈值、ICD 编码、呼吸困难/腹痛/发热、Neo4j 导出、专科会诊、20 条人工抽检。
