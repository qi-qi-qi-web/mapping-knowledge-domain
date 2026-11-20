# M1-05 双人盲评包

- 生成日期：2026-11-20
- 抽样总体：192 条事实
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

- 事实：抗凝治疗（`int.anticoagulation`） --治疗--> 急性肺栓塞（`cond.ape`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§5.3 急性肺栓塞
- 引文：> 尽快进行抗凝治疗
- 限定条件：`urgency`=immediate

### M105-02

- 事实：急性肺栓塞（`cond.ape`） --典型去向--> 住院（`disp.admit`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§5.3 急性肺栓塞
- 引文：> 中低危组：应住院或门诊抗凝治疗
- 限定条件：`context`=中低危组；应住院或门诊抗凝治疗

### M105-03

- 事实：急性心力衰竭（`cond.acute_heart_failure`） --表现为--> 端坐呼吸（`find.orthopnea`）
- 来源：呼吸困难（`src.msd.dyspnea.2025`）
- 定位：病因（表：引起急性呼吸困难的部分病因）
- 引文：> 端坐呼吸或夜间阵发性呼吸困难
- 限定条件：`typicality`=typical

### M105-04

- 事实：Ⅱ级 急重（`level.cn4.2`） --级别判定依据--> 类似心脏因素的胸痛（`find.cardiac_like_chest_pain`）
- 来源：急诊预检分诊专家共识（`src.cn.triage.2018`）
- 定位：§3 表 1 急诊预检分诊分级标准
- 引文：> 类似心脏因素的胸痛
- 限定条件：`criterion_type`=artificial

### M105-05

- 事实：呼吸困难（`cc.dyspnea`） --可能提示--> 急性肺栓塞（`cond.ape`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§5.3 急性肺栓塞
- 引文：> APE常伴呼吸困难或咯血
- 限定条件：`risk`=high

### M105-06

- 事实：急性肺栓塞（`cond.ape`） --危险信号--> 氧饱和度下降（`find.hypoxemia`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.2 症状
- 引文：> 常同时合并氧饱和度下降

### M105-07

- 事实：Ⅳ级 亚急症（`level.cn4.4`） --归属--> 普通诊疗区（`area.general`）
- 来源：急诊预检分诊专家共识（`src.cn.triage.2018`）
- 定位：§4 急诊分级分区管理；表 2
- 引文：> Ⅳ级患者在普通诊疗区顺序就诊

### M105-08

- 事实：胸痛中心（`proc.chest_pain_center`） --参与角色--> 心内科（`dept.cardiology`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§6 胸痛中心建设
- 引文：> 院前急救、急诊科和心内科是胸痛中心建设的主要参与者

### M105-09

- 事实：急性冠状动脉综合征（`cond.acs`） --推荐检查--> 动脉血气分析（`test.arterial_blood_gas`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§4.2.5 动脉血气分析
- 引文：> 高危胸痛患者可通过血气分析快速评估患者循环灌注情况
- 限定条件：`context`=高危胸痛循环灌注评估

### M105-10

- 事实：β受体阻滞剂（`int.beta_blocker`） --治疗--> 急性冠状动脉综合征（`cond.acs`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§5.1.4 ACS的药物治疗
- 引文：> 无禁忌证的患者应在发病24 h内常规服用，并逐渐加量
- 限定条件：`context`=无禁忌证者发病24 h内

### M105-11

- 事实：急性肺栓塞（`cond.ape`） --推荐检查--> 脑钠肽/氨基末端脑钠肽前体（`test.bnp`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§5.3 急性肺栓塞
- 引文：> APE患者入院后须尽快完成心电图检查，并行血气分析、D-二聚体、BNP、cTn等检测
- 限定条件：`priority`=urgent

### M105-12

- 事实：急性冠状动脉综合征（`cond.acs`） --危险因素--> 吸烟史（`risk.smoking`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.1 病史
- 引文：> 是否有高血压病、糖尿病、血脂异常、吸烟史、冠心病家族史等心血管危险因素

### M105-13

- 事实：ESI 2级 高危/不能等待（`level.esi.2`） --级别判定依据--> 危险区生命体征：<3月（HR>180、RR>50、SaO2<92%）（`crit.esi.danger_vitals_infant`）
- 来源：Emergency Severity Index, Version 4: Implementation Handbook（`src.us.ahrq.esi.v4.2005`）
- 定位：Chapter 6, Figure 6-1, p. 41
- 引文：> <3 m >180 >50
- 限定条件：`criterion_type`=algorithm

### M105-14

- 事实：CT血管造影（`test.cta`） --检查产出--> 主动脉内膜片（`find.intimal_flap`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§4.5 CT及CT血管造影（CTA）检查
- 引文：> 血管内膜征，主动脉管腔内发现动脉内膜片提示夹层或壁间血肿

### M105-15

- 事实：发热（`cc.fever`） --可能提示--> 肺炎（`cond.pneumonia`）
- 来源：呼吸困难（`src.msd.dyspnea.2025`）
- 定位：病因（表：引起急性呼吸困难的部分病因）
- 引文：> 肺炎 发热、咳痰、呼吸困难、有时胸膜炎性胸痛
- 限定条件：`risk`=high

### M105-16

- 事实：氧饱和度下降（`find.hypoxemia`） --支持--> 急性肺栓塞（`cond.ape`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.2 症状
- 引文：> 常同时合并氧饱和度下降
- 限定条件：`strength`=moderate

### M105-17

- 事实：急诊严重度指数（ESI）第4版（`scale.esi_v4_2005`） --分诊级别--> ESI 4级 需1项资源（`level.esi.4`）
- 来源：Emergency Severity Index, Version 4: Implementation Handbook（`src.us.ahrq.esi.v4.2005`）
- 定位：Chapter 2, The Emergency Severity Index (ESI)
- 引文：> The Emergency Severity Index (ESI) is a five-level triage scale

### M105-18

- 事实：急性肺栓塞（`cond.ape`） --需鉴别--> 张力性气胸（`cond.tension_pneumothorax`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.2 症状
- 引文：> APE常伴呼吸困难或咯血，常同时合并氧饱和度下降，甚或晕厥、猝死；张力性气胸患者表现为极度呼吸困难，缺氧严重者出现发绀、甚至窒息

### M105-19

- 事实：张力性气胸（`cond.tension_pneumothorax`） --表现为--> 突发极度呼吸困难（`find.severe_sudden_dyspnea`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.2 症状
- 引文：> 张力性气胸患者表现为极度呼吸困难
- 限定条件：`typicality`=typical

### M105-20

- 事实：急性肺栓塞（`cond.ape`） --鉴别依据--> 氧饱和度下降（`find.hypoxemia`）
- 来源：急性胸痛急诊诊疗专家共识（`src.cn.chest_pain.2019`）
- 定位：§3.2.2 症状
- 引文：> 常同时合并氧饱和度下降

## 判定规则

- `correct`：主体、关系、客体和限定条件都得到引文支持，且没有明显临床歧义。
- `partial`：核心关系对，但缺少重要限定，或引文只间接支持，或表述不够精确。
- `error`：引文不支持该关系，主客体错误，或关系方向错误。

本包只用于评审准备；在两名独立人类完成评审前，M1-05 不得标记为通过。
