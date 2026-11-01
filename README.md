# ED-ConsultKG

**急诊全流程会诊知识图谱**（Emergency Department full-process Consultation Knowledge Graph）。

当前状态：**M1 进行中 / 胸痛单主诉 + ESI v4 五级**。94 实体、129 事实，全部 `ai-draft`，未经临床专家审核；只用于研究与智能体检索实验，**不得用于真实患者诊疗**。

## 这是什么

- 一个**流程感知**的急诊知识图谱 Schema：分诊 → 检查 → 鉴别 → 多学科会诊 → 处置 → 转归；
- 一个**来源可审计**的胸痛种子图谱：每条事实带来源、章节定位、原文短引文、审核状态；
- 一个**零第三方依赖**的工具链：Schema/数据校验、引文审计、来源核验、查询 CLI、单元测试、CI；
- 一份**可持续构建**的治理文档：[`Agent.md`](Agent.md)、[`docs/PLAN.md`](docs/PLAN.md)、[`DEVLOG.md`](DEVLOG.md)、[`TODO.md`](TODO.md)。

## 不是什么

- 不是临床决策系统，不提供诊断/治疗建议；
- 不是“大规模”图谱：当前只有胸痛一个主诉 + 两套分诊量表；
- 不是 LLM 自动抽取产物：当前为人工按来源抽取，逐条引文审计；
- 不包含 MIMIC/患者数据、不包含指南全文、**不做中国四级与 ESI 五级的互相映射**。

## 快速开始

要求 Python ≥3.10，无第三方依赖。

```bash
# Windows PowerShell 建议先设置 UTF-8
$env:PYTHONUTF8=1

# 校验 Schema/来源/实体/事实
python -m edkg validate --strict

# 查看规模与质量指标
python -m edkg stats

# 查询胸痛路径（文本 / JSON）
python -m edkg query --complaint 胸痛
python -m edkg query --complaint 胸痛 --json
# 只看法定量表之一（两套量表独立，不互映射）
python -m edkg query --complaint 胸痛 --scale cn_4level_2018
python -m edkg query --complaint 胸痛 --scale esi_v4_2005

# 测试
python -m unittest discover -s tests -v

# 联网核验来源与引文（发布前）
python scripts/verify_sources.py
python scripts/audit_quotes.py
```

## 仓库结构

```text
Agent.md                    构建行为准则（数据真实性/审核/提交/DoD）
DEVLOG.md                   变更记录
TODO.md                     分阶段待办
docs/PLAN.md                总体构建方案、路线图、评估
docs/SCHEMA.md              Schema 人读说明
docs/MVP.md                 胸痛 MVP 说明
docs/research/              原始研究报告 + 图（设计输入，非数据源目录）
schema/edkg.schema.json     Schema v0.2
data/registry/sources.json  来源登记与核验记录
data/kg/entities.jsonl      实体（94）
data/kg/facts.jsonl         事实（129，带 provenance）
edkg/                       校验/查询/统计 CLI
scripts/                    来源核验、引文审计
tests/                      35 项单元测试
.github/workflows/ci.yml    离线 CI
```

## 数据真实性

当前使用三份**已核验、可访问**的来源：

| 来源 | 链接 | 用途 |
|---|---|---|
| 急性胸痛急诊诊疗专家共识（2019） | http://mc.cem.org.cn/rhtml/20190402/index.htm | 胸痛病因、危险分层、检查、治疗、胸痛中心 |
| 急诊预检分诊专家共识（2018） | http://mc.cem.org.cn/rhtml/20180606/index.htm | 中国四级分诊、响应时限、分区 |
| AHRQ ESI v4 Implementation Handbook（2005，公有领域） | https://permanent.access.gpo.gov/lps46616/lps46616/www.ahrq.gov/research/esi/esihandbk.pdf | ESI 五级、资源需求、危险区规则 |

- 只保存**短引文 + 章节定位**，不转载全文/PDF（AHRQ 公有领域，但仍只存抽取事实）；
- `candidate` 来源（MIMIC-IV-ED、DDXPlus、TriageAgent、PrimeKG、ICD-10）只登记、**不进入事实**；
- 报告中的 arXiv/数据集引用未逐条核验，不作为数据源；见 [`docs/research/README.md`](docs/research/README.md)；
- 事实只能引用 `verified` 来源；`python scripts/audit_quotes.py` 逐条回查原文（当前：129/129 通过）。
- **中国四级与 ESI 五级分别建模，不互映射**；查询默认分组展示，也可用 `--scale` 只看一套。

## 当前质量指标

| 指标 | 结果 |
|---|---|
| Schema 校验（strict） | 0 错误 / 0 警告 |
| 实体 / 事实 | 94 / 129 |
| provenance 完整率 | 100% |
| 重复三元组 | 0 |
| 引文审计 | 129/129 命中 |
| 开放来源核验 | 3/3 HTTP 200 |
| 单元测试 | 35 项通过 |
| CI（GitHub Actions） | [见 Actions](https://github.com/qi-qi-qi-web/mapping-knowledge-domain/actions) |
| 临床审核 | **未做**（全部 ai-draft） |

## 路线图

- **M1（进行中）**：ESI 五级已完成（5 级/8 指标/资源规则）；待办：危险区年龄分层阈值、ICD-10 编码、呼吸困难/腹痛/发热、Neo4j 导出、专科会诊、20 条抽检；
- **M2**：10 主诉、30+ 高危病种、LLM 候选抽取 + HITL、L1/L2 评估；
- **M3**：大规模扩展、GraphRAG/路径检索、DDXPlus/MIMIC 评测、论文产出。

详见 [`docs/PLAN.md`](docs/PLAN.md) 与 [`TODO.md`](TODO.md)。

## 许可与免责声明

- 代码：MIT（见 [`LICENSE`](LICENSE)）；
- 原创文档/数据：CC BY-NC 4.0；第三方摘录以来源条款为准（见 [`NOTICE.md`](NOTICE.md)）；
- 本项目仅供科研与教学，不构成医疗建议、诊断或治疗方案；任何面向真实患者的应用须经伦理审查、监管审批与医生全程监督。

## 引用

本仓库的选题与设计输入来自 [`docs/research/大规模急诊全流程会诊知识图谱研究报告.md`](docs/research/大规模急诊全流程会诊知识图谱研究报告.md)。该报告是研究综述，不是经过逐条核验的数据源目录。
