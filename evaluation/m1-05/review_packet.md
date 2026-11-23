# M1-05 双人盲评包

- 生成日期：2026-11-23
- 抽样总体：188 条事实
- 样本量：20
- 随机种子：20261120
- 抽样方法：predicate-stratified: one fact per predicate stratum, then five additional facts from the largest strata; within-stratum random selection; item order shuffled

## 评审说明

请两名评审者各自独立完成，不要互相讨论，也不要查看 `sample_manifest.json`。
每条事实只判断三选一：`correct`（正确）、`partial`（部分正确）、`error`（错误）。
依据页面给出的来源、定位和引文判断；不要用自身记忆补全引文未支持的内容。
评审者 A 填 `review_a.csv`，评审者 B 填 `review_b.csv`；不要交换或覆盖文件。

## 待评事实

### M105-01

- 事实：急性主动脉夹层（`cond.aad`） --典型去向--> 转诊至具备能力医院（`disp.transfer`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§5.2 急性主动脉夹层
- 引文：> 不具备大血管介入和手术能力的医疗机构，应当建立完善的急性主动脉夹层转诊机制
- 限定条件：`context`=不具备大血管介入和手术能力

### M105-02

- 事实：中国急诊预检分诊四级标准（2018）（`scale.cn_4level_2018`） --分诊级别--> Ⅱ级 急重（`level.cn4.2`）
- 来源：急诊预检分诊专家共识（`src.cn.triage.2018`）
- 定位：§3.1 预检分诊级别
- 引文：> 本标准按病情危急程度分为四级

### M105-03

- 事实：脑膜炎（`cond.meningitis`） --危险信号--> 瘀点/紫癜样皮疹（`find.petechial_rash`）
- 来源：发热（`src.msd.fever.2026`）
- 定位：临床表现解析（危险信号）
- 引文：> 头痛，颈部僵硬，出现瘀斑或紫癜样皮疹很可能是 脑膜炎 。
- 限定条件：`note`=发热伴瘀点/紫癜样皮疹提示脑膜炎

### M105-04

- 事实：Ⅳ级 亚急症（`level.cn4.4`） --归属--> 普通诊疗区（`area.general`）
- 来源：急诊预检分诊专家共识（`src.cn.triage.2018`）
- 定位：§4 急诊分级分区管理；表 2
- 引文：> Ⅳ级患者在普通诊疗区顺序就诊

### M105-05

- 事实：胸痛（`cc.chest_pain`） --可能提示--> 急性冠状动脉综合征（`cond.acs`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§1 急性胸痛救治现状
- 引文：> 不仅包括急性冠状动脉综合征（acute coronary syndrome，ACS）
- 限定条件：`risk`=high

### M105-06

- 事实：直接经皮冠状动脉介入治疗（`int.pci`） --治疗--> 急性冠状动脉综合征（`cond.acs`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§5.1.1 急性ST段抬高型心肌梗死
- 引文：> 包括直接PCI（primary PCI，PPCI）、转运PCI或静脉溶栓治疗
- 限定条件：`context`=STEMI再灌注, `urgency`=immediate

### M105-07

- 事实：胸痛中心（`proc.chest_pain_center`） --参与角色--> 急诊科（`dept.emergency`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§6 胸痛中心建设
- 引文：> 院前急救、急诊科和心内科是胸痛中心建设的主要参与者

### M105-08

- 事实：胸痛（`cc.chest_pain`） --推荐检查--> 动脉血气分析（`test.arterial_blood_gas`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§4.2.5 动脉血气分析
- 引文：> 高危胸痛患者可通过血气分析快速评估患者循环灌注情况
- 限定条件：`context`=高危胸痛循环灌注评估

### M105-09

- 事实：抗凝治疗（`int.anticoagulation`） --治疗--> 急性肺栓塞（`cond.ape`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§5.3 急性肺栓塞
- 引文：> 尽快进行抗凝治疗
- 限定条件：`urgency`=immediate

### M105-10

- 事实：CT血管造影（`test.cta`） --检查产出--> 主动脉内膜片（`find.intimal_flap`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§4.5 CT及CT血管造影（CTA）检查
- 引文：> 血管内膜征，主动脉管腔内发现动脉内膜片提示夹层或壁间血肿

### M105-11

- 事实：Ⅲ级 急症（`level.cn4.3`） --级别判定依据--> 中等程度的非心源性胸痛（`find.moderate_noncardiac_chest_pain`）
- 来源：急诊预检分诊专家共识（`src.cn.triage.2018`）
- 定位：§3 表 1 急诊预检分诊分级标准
- 引文：> 中等程度的非心源性胸痛
- 限定条件：`criterion_type`=artificial

### M105-12

- 事实：急性肺栓塞（`cond.ape`） --表现为--> 晕厥（`find.syncope`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.2 症状
- 引文：> 甚或晕厥、猝死
- 限定条件：`typicality`=variable

### M105-13

- 事实：急性冠状动脉综合征（`cond.acs`） --危险因素--> 血脂异常（`risk.dyslipidemia`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.1 病史
- 引文：> 是否有高血压病、糖尿病、血脂异常、吸烟史、冠心病家族史等心血管危险因素

### M105-14

- 事实：心电图提示急性心肌梗死（`find.ecg_acute_mi`） --支持--> 急性心肌梗死（`cond.acute_mi`）
- 来源：急诊预检分诊专家共识（`src.cn.triage.2018`）
- 定位：§3 表 1 急诊预检分诊分级标准
- 引文：> ECG提示急性心肌梗死
- 限定条件：`strength`=strong

### M105-15

- 事实：急性胆囊炎（`cond.cholecystitis`） --推荐检查--> 腹部超声（`test.abdominal_ultrasound`）
- 来源：急性腹痛（`src.msd.acute_abdominal_pain.2024`）
- 定位：检查
- 引文：> 若疑似胆道疾病或异位妊娠（经阴道探头）以及儿童疑似阑尾炎，应行超声检查。
- 限定条件：`priority`=urgent, `timing`=unspecified

### M105-16

- 事实：急性冠状动脉综合征（`cond.acs`） --需鉴别--> 急性肺栓塞（`cond.ape`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.2 症状
- 引文：> ACS症状主要包括发作性胸部闷痛、压迫感或憋闷感，甚或濒死感，部分患者可放射至上肢、后背部或颈部，劳累、情绪激动、气候骤变等均可诱发，持续数分钟至数十分钟，休息或硝酸甘油可缓解，持续时间超过20 min未缓解，需考虑急性心肌梗死的可能性；AAD及大血管疾病多表现为持续撕裂样胸、背痛，可伴血压明显升高、双侧肢体血压差别较大等；APE常伴呼吸困难或咯血，常同时合并氧饱和度下降，甚或晕厥、猝死

### M105-17

- 事实：胸痛（`cc.chest_pain`） --可能提示--> 急性肺栓塞（`cond.ape`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§1 急性胸痛救治现状
- 引文：> 以急性肺栓塞（acute pulmonary embolism，APE）为主的“急性肺动脉综合征”
- 限定条件：`risk`=high

### M105-18

- 事实：张力性气胸（`cond.tension_pneumothorax`） --鉴别依据--> 突发极度呼吸困难（`find.severe_sudden_dyspnea`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.2 症状
- 引文：> 张力性气胸患者表现为极度呼吸困难

### M105-19

- 事实：急性冠状动脉综合征（`cond.acs`） --表现为--> 胸部闷痛、压迫感或憋闷感（`find.chest_pressure`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.2 症状
- 引文：> 发作性胸部闷痛、压迫感或憋闷感
- 限定条件：`typicality`=typical

### M105-20

- 事实：ESI 4级 需1项资源（`level.esi.4`） --级别判定依据--> 预计需要1项资源（`crit.esi.resources_1`）
- 来源：Emergency Severity Index, Version 4: Implementation Handbook（`src.us.ahrq.esi.v4.2005`）
- 定位：Chapter 5, Expected Resource Needs
- 引文：> those who are likely to require one resource are level 4
- 限定条件：`criterion_type`=algorithm

## 判定规则

- `correct`：主体、关系、客体和限定条件都得到引文支持，且没有明显临床歧义。
- `partial`：核心关系对，但缺少重要限定，或引文只间接支持，或表述不够精确。
- `error`：引文不支持该关系，主客体错误，或关系方向错误。

本包只用于评审准备；在两名独立人类完成评审前，M1-05 不得标记为通过。
