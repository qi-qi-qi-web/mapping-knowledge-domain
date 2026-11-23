# M1-05 round 1 历史记录

状态：**未通过；仅作内部质量反馈，不是临床验证。**

本目录保留 2026-11-23 的 round 1 样本、两份评审 CSV 与评估报告，目的是可追溯，不是把结果当作验收证据。

## 文件

- `sample.json`、`sample_manifest.json`、`review_packet.md`、`review_template.csv`：round 1 的 20 条样本（从当时 192 条事实中抽取）。
- `review_a.csv`、`review_b.csv`：用户提供的两份评分；只有 `sample_id,verdict,comment`，没有评审者姓名/角色。
- `report.json`：`scripts/m1_05_evaluate.py --json` 的输出。

## 结果

- 评审 A：correct 13、partial 7、error 0；strict 65.0%、lenient 82.5%。
- 评审 B：correct 17、partial 3、error 0；strict 85.0%、lenient 92.5%。
- observed agreement 60.0%；Cohen's kappa -0.0127；unanimous correct 11/20（55.0%）。
- gate 未通过（最低严格正确率 65.0%，unanimous correct 55.0%）。

## 评审反馈摘要

- A：没有判定为 error；partial 主要集中在两类问题：限定条件过度延伸（`risk=high`、`strength=moderate` 等引文未定级），以及关系标签功能性拔高（把描述性发现写成“危险信号”“需鉴别”“鉴别依据”）。
- B：`M105-02` 的“住院或门诊”并列选项被压成单一处置；`M105-09` 的主体从“高危胸痛”漂移到 ACS；`M105-17` 的“1 项资源”缺少对应引文。
- 两位评审都认为已核验的外部引文（分诊指标、β受体阻滞剂、APE 检测清单、ESI 危险区生命体征）与原文一致，未发现伪造或错置。

## 重要限制

- 评审 CSV 没有姓名、角色或独立性声明；**不能确认这是两名独立临床人员完成的盲评**。
- 因此本报告不能作为 M1-05 的通过证据，也不能用于声称正确率/Kappa 已达到临床验收标准。
- round 1 的样本已被数据修正取代；这些评分不得套用到 round 2 的 `evaluation/m1-05/sample.json`。
- 全部事实仍为 `ai-draft`；本目录不构成临床审核或诊疗建议。
