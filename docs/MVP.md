# 急诊 4 主诉 MVP（M0 + M1）

> 状态：研究用最小可行版本 + ESI v4 增量；所有事实 `ai-draft`，未经临床专家审核，不得用于真实患者诊疗。

## 1. 为什么从胸痛开始

- 急诊最常见、时间依赖性最强的主诉之一；
- 高危鉴别（ACS/AAD/APE/张力性气胸）明确，适合验证“流程感知 + 鉴别”；
- M0 已核验的三份事实来源（两份中文共识 + AHRQ ESI v4）提供了分诊、危险分层、检查、治疗、MDT 与五级分诊的完整段落；WHO ICD-10 另用于 9 个病种的编码映射，不进入事实。
- M1-03 在胸痛之外增加呼吸困难、腹痛、发热 3 个主诉，来源为 3 份 MSD 诊疗手册专业版页面；仍只使用短引文，不转载全文。

## 2. 范围

| 维度 | 内容 |
|---|---|
| 主诉 | 胸痛、呼吸困难、腹痛、发热 |
| 高危病种 | 胸痛：急性冠脉综合征、急性心肌梗死、急性主动脉夹层、急性肺栓塞、张力性气胸；呼吸困难：急性肺栓塞、张力性气胸、急性心力衰竭、肺炎；腹痛：急性胰腺炎、急性阑尾炎；发热：脓毒症、肺炎、脑膜炎 |
| 中低危示例 | 胸痛：稳定性冠心病、胃食管反流病、急性肋软骨炎、神经官能症；呼吸困难：哮喘急性发作；腹痛：急性胆囊炎；发热：病毒性上呼吸道感染 |
| 分诊 | 中国四级标准（Ⅰ–Ⅳ + 非急症）+ ESI v4 五级（含 4 个年龄分层危险区阈值）；两套独立，不互映射 |
| 检查 | 胸痛：心电图、hs-cTn、CK-MB、肌红蛋白、D-二聚体、BNP、血气、胸片、CTA、床旁超声、Wells、PESI；呼吸困难：胸片、心电图、血气、BNP、CTA、超声心动图；腹痛：脂肪酶、尿妊娠试验、腹部超声、腹部CT、腹部平片；发热：血培养、尿培养、胸片、腰穿、头颅CT、血常规 |
| 治疗 | 胸痛：PCI、溶栓、抗血小板、抗凝、β受体阻滞剂、镇痛、胸腔穿刺减压、胸腔闭式引流；腹痛：急诊手术、镇痛；发热：经验性抗生素 |
| 组织 | 胸痛中心（院前急救/急诊科/心内科）；不具备 PCI/大血管手术/引流能力时转诊 |
| 编码 | WHO ICD-10：9 个胸痛病种（8 个编码，ACS 无单一码）；仅检索/追溯，不用于临床编码/计费；M1-03 新病种未填 ICD-10 |
| 图谱导出 | Neo4j CSV/Cypher：135 节点、188 关系、13 类节点、15 个谓词；`queries/` 10 个只读用例；离线与 JSONL 参考结果一致，未在真实 Neo4j 实例执行 |
| 规模 | 135 实体、188 事实（M0 80/116 + M1 ESI 18/17 + M1-03 37/59，M1-05 round 1 修正 -4） |

## 3. 来源与定位

| 来源 | 使用的章节 |
|---|---|
| `src.cn.chest_pain.2019` | §1 病因；§3.1 分诊策略；§3.2 危险分层（病史/症状/查体/辅助检查）；§3.3.3 非心源性鉴别；§4.1–4.5 检查；§5.1–5.4 治疗；§6 胸痛中心 |
| `src.cn.triage.2018` | §3/表 1 四级标准与响应时限；§4/表 2 分区；§3.1 级别定义 |
| `src.us.ahrq.esi.v4.2005` | ESI 五级定义；Decision Point A/B；资源需求；危险区规则（Figure 3-1/6-1） |
| `src.who.icd10.2019` | 9 个病种的 `GetConcept?ConceptId=…` 页面（编码 registry，不进入事实） |
| `src.msd.dyspnea.2025` | MSD 呼吸困难页：病种/表现/检查（M1-03） |
| `src.msd.acute_abdominal_pain.2024` | MSD 急性腹痛页：病种/表现/检查/处置（M1-03） |
| `src.msd.fever.2026` | MSD 发热页：病种/表现/检查/经验性治疗（M1-03） |

已用于编码映射：WHO ICD-10（9 个病种 / 8 个编码，ACS 无单一码，见 `data/registry/icd10.json`）。
未使用：MIMIC/DDXPlus（后评测）、CMeKG/PrimeKG（候选）。
危险区阈值：HR/RR 有文本引文；SaO2<92% 为 Figure 6-1 图像目视转录（裁剪图见 `docs/research/figures/esi_fig6_1_danger_zone.png`）。

## 4. 查询

```bash
# 文本
python -m edkg query --complaint 胸痛
python -m edkg query --complaint 呼吸困难
python -m edkg query --complaint 腹痛
python -m edkg query --complaint 发热

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

## 4.1 Neo4j/Cypher 导出（可选）

```bash
python scripts/export_neo4j.py --out neo4j
python scripts/verify_neo4j_queries.py
```

- 生成 13 类实体、15 个谓词的 28 个 CSV，以及 `neo4j/setup.cypher`、`neo4j/import.cypher`；不依赖 APOC。
- `queries/` 提供 10 个只读用例，覆盖主诉鉴别、高危病种、红旗、检查、治疗、分诊、ICD-10、病种证据与来源覆盖。
- `verify_neo4j_queries.py` 在**不连接 Neo4j** 的情况下，用 Python 参考实现核对 `queries/expected.json`；本机无 Neo4j，未做真实实例导入。
- 详细说明见 [`queries/README.md`](queries/README.md) 与 [`neo4j/README.md`](neo4j/README.md)。

## 4.2 M1-05 双人评审包（等待人类评审）

```bash
python scripts/m1_05_sample.py
# 两名独立人类填写 review_a.csv / review_b.csv 后：
python scripts/m1_05_evaluate.py --a evaluation/m1-05/review_a.csv --b evaluation/m1-05/review_b.csv --json
```

- 20 条事实按 predicate 分层，固定 seed `20261120`；`sample.json`/`review_packet.md` 不含 `fact_id` 或置信度。
- 评审材料与说明见 [`../evaluation/m1-05/README.md`](../evaluation/m1-05/README.md)；在两名独立人类完成前没有正确率/Kappa 结论，M1-05 不得标记为通过。
- 评估器拒绝两份完全相同的评分文件；gate 未过应修数据，不得改指标或伪造评审。

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
  - 指标: 危险区生命体征：<3月（HR>180、RR>50、SaO2<92%）（algorithm/vital_sign） [ev71]
  - 指标: 危险区生命体征：3月–3岁（HR>160、RR>40、SaO2<92%）（algorithm/vital_sign） [ev72]
...
```

（实际输出以 `python -m edkg query --complaint 胸痛` 为准；evidence id 会随数据增删变化。）

## 6. 质量门

- `python -m edkg validate --strict`：0 错误 0 警告；
- `python -m unittest discover -s tests -v`：61 项通过；
- `python scripts/audit_quotes.py`：事实 188/188 + ICD-10 9/9 引文命中（2026-11-23）；
- `python scripts/verify_sources.py`：7/7 开放来源 HTTP 200；
- `python scripts/verify_neo4j_queries.py`：10 个 Cypher 用例与 JSONL 参考结果一致（离线，未执行 Neo4j）；
- M1-05：round 1 已运行但 gate 未通过（A 65%、B 85%、κ -0.0127），评审者身份未记录，只作内部历史；已修正 4 条事实并重抽 round 2 样本；**双人人类评审未完成，无质量通过结论**；
- 事实引用 6 个 `verified` 来源；WHO ICD-10 仅用于编码映射；0 重复三元组；provenance 100%。

## 7. 已知限制

- **未临床审核**：全部 `ai-draft`；不能用于真实患者。
- **两套量表不互映射**：中国四级与 ESI 五级分别建模；未做、也不做未经专家论证的交叉映射。
- **ESI 危险区阈值**：HR/RR 有 `pdftotext -raw` 文本引文；SaO2<92% 为 Figure 6-1 图像目视转录（旋转文本未被 pdftotext 完整抽取），已附公有领域裁剪图；不是凭记忆补的数字。
- **ICD-10 仅覆盖 9 个胸痛病种**：8 个编码，ACS 为 `no_single_code`；只用于知识检索/来源追溯，不用于临床编码/计费，且未经临床编码员审核；M1-03 新病种未填 ICD-10。
- **会诊较薄**：只写胸痛中心参与科室与转诊条件，未写病种级专科会诊。
- **低危病种结构化不足**：胸痛的稳定性冠心病/胃食管反流病/肋软骨炎/神经官能症目前只有“主诉可能提示”一条事实；新主诉的低危病种也只作了最小挂接。
- **流程层未实例化**：Visit/CareEvent 只有 Schema，没有患者事件。
- **规模小**：135/188，不是“大规模”；规模目标见 `docs/PLAN.md`。
- **新主诉分诊未扩展**：M1-03 未新增中国四级/ESI 的病种级分诊指标，非胸痛主诉的分诊输出只保留通用算法指标。
- **Neo4j 未实测**：本机无 Neo4j/`cypher-shell`，Docker daemon 未启动，`dist.neo4j.org` 返回 403；M1-04 仅完成确定性导出、10 个查询用例的静态检查与 JSONL 参考结果比对，**未在真实 Neo4j 实例执行导入/查询**，也没有性能数据。
- **M1-05 未完成**：round 1 的 20 条评审 gate 未通过且评审者身份/独立性未记录；已修正 4 条引文不支持的关系/处置事实，事实数 192→188，round 2 样本已重抽，但尚无两名独立人类评审；**没有质量通过结论**，不得声称质量验收通过；受 B-01 阻塞。

## 8. 下一步

见 `TODO.md` 的 M1：先完成 M1-05 双人独立人类评审（B-01），再考虑病种级专科会诊；不得用 AI 自查替代评审。
