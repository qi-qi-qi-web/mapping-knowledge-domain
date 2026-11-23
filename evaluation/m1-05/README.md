# M1-05 质量评估包

状态：**round 1 未通过；数据已按评审反馈修正；round 2 样本已重抽，等待两名独立人类评审。尚未产生质量结论。**

M1-05 的验收要求是 20 条分层随机事实由两名评审独立判定为“正确 / 部分正确 / 错误”，报告正确率、P/R/F1 与 Kappa，并达到 ≥90% 的正确率。项目当前受 `TODO.md` 的 B-01（临床专家双人盲评）阻塞：在两名独立人类完成评审前，不得把 M1-05 标记为通过，也不得用 AI 自查或两个 AI 代理冒充人类盲评。

## 当前文件（round 2）

- `sample.json`：从修正后的 188 条事实中抽取的 20 条评审样本；只含样本 ID、主体/关系/客体、限定条件、来源、定位、引文，不含 `fact_id` 与置信度。
- `sample_manifest.json`：`sample_id -> fact_id` 审计映射，**评审期间不应展示给评审者**。
- `review_packet.md`：可直接发给评审者的说明与 20 条待评事实。
- `review_template.csv`：空白评分表，列为 `sample_id,verdict,comment`。
- `README.md`：本文件。
- `round-1/`：round 1 的样本、评审 CSV、评估报告与历史说明；**不得把 round-1 的评分套用到 round-2 样本**。

`sample.json` 与 `review_packet.md` 由固定 seed 生成；重新运行会得到同一组样本（`generated_on` 日期除外）。不要手工修改样本；如需重抽样，先记录 seed 与原因。

## round 1 结果（历史）

round 1 的 20 条样本已由用户提供 `review_a.csv` / `review_b.csv` 并运行评估器；结果见 `round-1/report.json`：

- 评审 A：correct 13、partial 7、error 0；strict 65.0%、lenient 82.5%。
- 评审 B：correct 17、partial 3、error 0；strict 85.0%、lenient 92.5%。
- observed agreement 60.0%；Cohen's kappa **-0.0127**；unanimous correct 11/20（55.0%）。
- gate **未通过**（最低严格正确率 65.0%，unanimous correct 55.0%）。

**身份与独立性说明：** 这两份 CSV 没有评审者姓名/角色记录；用户说明了判定理由，但没有确认两人是独立临床人员。因此该结果只作为**内部质量反馈/历史记录**，不能作为 M1-05 的临床验证证据，也不能据此声称正确率或 Kappa 已达标。

## round 2 前的修正

根据 round 1 的反馈，仓库已修正以下**有明确引文或关系标签依据**的问题，并保持全部事实仍为 `ai-draft`：

- 删除 `fact.ape.red_flag.hypoxemia`：引文只描述“氧饱和度下降”，未将其定义为危险信号。
- 删除 `fact.ape.distinguished_by.hypoxemia`：引文没有说明该发现可鉴别 APE。
- 删除 `fact.ape.differentiated_from.tension`：引文只并列描述 APE 与张力性气胸，未说明“需鉴别”。
- 删除 `fact.ape.disposition.admit`：引文写“应住院或门诊抗凝治疗”，不能把住院作为唯一典型处置。
- 将血气分析建议的主体从 `cond.acs` 改为 `cc.chest_pain`，与引文的“高危胸痛患者”一致。
- 修正 5 条 ESI `HAS_LEVEL` 的引文，分别使用定义各级资源需求的原文；不再用“五级分诊量表”这一总述支撑每一级。
- 删除 `fact.hypoxemia.supports.ape` 的 `strength=moderate` 限定，以及 `fact.dyspnea.may_indicate.ape`、`fact.fever.may_indicate.pneumonia` 的 `risk=high` 限定：这些限定没有被引文直接定级。

事实总数由 192 变为 188。修正不是“让指标通过”的调参，而是删除/收窄引文不支持的断言；round 2 必须重新独立评审。

## 评审流程

1. 把 `review_packet.md` 和一份 `review_template.csv` 副本分别交给评审者 A、B；两人不讨论、不交换评分。
2. 评审者把副本命名为 `review_a.csv` / `review_b.csv`，逐条填写：
   - `correct`：主体、关系、客体和限定条件均得到引文支持，且无明显临床歧义。
   - `partial`：核心关系成立，但缺少重要限定、引文只间接支持或表述不够精确。
   - `error`：引文不支持、主客体错误或关系方向错误。
   - `comment` 可写简短理由；**不要填写患者信息**。
3. 评审者不要查看 `sample_manifest.json`，也不要参考另一名评审者的评分。
4. 将两份 CSV 放回本目录，运行评估：

```bash
python scripts/m1_05_evaluate.py \
  --sample evaluation/m1-05/sample.json \
  --a evaluation/m1-05/review_a.csv \
  --b evaluation/m1-05/review_b.csv \
  --json > report.json
```

退出码：`0` 通过、`1` 未达 gate、`2` 输入缺失/格式错误/两份文件完全相同。评估器不会生成或修改评审意见。

## 指标与 gate

- 每位评审：`correct / partial / error` 计数、严格正确率、宽松正确率（`partial` 计 0.5）。
- 评审者间一致性：observed agreement、Cohen's kappa、unanimous correct/error、disagreements。
- P/R/F1：以 A 为参考/B 为预测及反向的逐类指标与 macro-F1；这是**评审者间一致性**，不是外部 gold standard 上的抽取性能。
- Gate：两位评审的严格正确率均 ≥0.9，且 `unanimous_correct_rate` ≥0.9。未通过时必须修数据，不得修改指标或样本以“凑通过”。

## 限制

- 本包是覆盖导向的分层样本，不是按事实总体患病率加权，不能外推为全图准确率。
- 样本只覆盖当前 188 条事实中的 20 条；结论仅对这 20 条负责。
- 全部事实仍为 `ai-draft`；M1-05 的人类评审也不能替代临床上线前的完整审核。
- 当前没有真实 Neo4j 实例参与本评估；M1-05 不评估图数据库性能。
- 在真实评审完成前，仓库中不得出现伪造的 `review_a.csv`、`review_b.csv` 或 `report.json`。
