# 药物情报报告：Osimertinib / 奥希替尼（泰瑞沙 TAGRISSO）— 美国 + 中国

> ⚠️ **仅供研发情报参考，非医疗建议、非投资建议。**
> 生成时间：2026-06-27（UTC）｜ 口径：**按适应症（治疗线/分期）逐个列** ｜ 数据脚本：`fetch_drug_data.py "Osimertinib" --max-studies 300`
> **徽标**：✅`<库>` 可核实 ｜ 🔍web 附URL ｜ ⚠️ 存疑/弱源 ｜ 🔴 高幻觉/必核 ｜ ❓N/A 查过未找到
> 🚧 本样例为一次性跑完的演示稿；正式运行时 G0/G1 为硬性暂停门，G2–G5 应停下等人工确认（见文末说明）。

---

## 0. 身份卡

| 字段 | 值 | 徽标 |
|------|----|------|
| INN | Osimertinib（游离碱）/ Osimertinib mesylate（甲磺酸盐，原料药盐型） | ✅PubChem / ✅ChEMBL |
| 中文名 | 奥希替尼 / 甲磺酸奥希替尼 | 🔍web（[az-cn](https://www.astrazeneca.com.cn/)）|
| 研究代号 | AZD9291（曾用 Mereletinib） | ✅PubChem(synonyms) |
| 商品名 | TAGRISSO（美）/ 泰瑞沙（中）| ✅openFDA(brand) / 🔍web |
| PubChem CID | 71496458 | ✅PubChem |
| ChEMBL ID | CHEMBL3353410（游离碱）、CHEMBL3545063（甲磺酸盐）| ✅ChEMBL |
| 分子式 | C28H33N7O2 | ✅PubChem |
| SMILES | `CN1C=C(C2=CC=CC=C21)C3=NC(=NC=C3)NC4=C(C=C(C(=C4)NC(=O)C=C)N(C)CCN(C)C)OC` | ✅PubChem |
| 结构图 | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/71496458/PNG | ✅PubChem |
| 类型 / max_phase | 小分子；ChEMBL max_phase = 4（已上市） | ✅ChEMBL |

---

## 1. 分子名确认
- 中英文互校通过：Osimertinib = 奥希替尼 = AZD9291 = TAGRISSO/泰瑞沙，同一实体（CID 71496458）。✅PubChem ✅ChEMBL
- ClinicalTrials.gov 按 intervention 检索命中 **380 条**试验（本次抓取 300 条用于统计）。✅ClinicalTrials.gov
- openFDA `drugsfda` 命中 **NDA208065**（generic_name = osimertinib）。✅openFDA
- 盐型说明：上市制剂为**甲磺酸盐**，剂量以游离碱计。✅ChEMBL(synonyms: "Osimertinib mesylate")
- chinadrugtrials.org.cn 检索：本次未经脚本抓取（无 API）→ 见步4/步7 的 🔍web/❓N/A 处理。

## 2. 厂家（区分 原研 / 权利人 / MAH）

| 地区 | 原研 | 当前权利人 / MAH | 徽标 |
|------|------|------------------|------|
| 🇺🇸 美国 | AstraZeneca | NDA208065 持有人 **AstraZeneca**（sponsor_name = ASTRAZENECA）| ✅openFDA |
| 🇨🇳 中国 | AstraZeneca | 上市许可持有人 **阿斯利康制药有限公司**（泰瑞沙）| 🔴 G5 / 🔍web（[az-cn 新闻稿](https://www.astrazeneca.com/content/az-cn-zh/media/press-releases/2025/01-02-01.html)）|

- CT.gov leadSponsor 以 AstraZeneca 为主，另有大量研究者发起试验（Fudan、复旦、四川百利等）。✅ClinicalTrials.gov
- 中国 MAH 名称需到 NMPA 数据库逐条核对（🔴 G5）。

## 3. MoA（作用机制）
- **第三代 EGFR-TKI，不可逆抑制剂**；对 EGFR 敏感突变（Ex19del、L858R）及 **T790M 耐药突变** 均有活性；对野生型 EGFR 选择性较高。
- ✅ChEMBL `mechanism_of_action` = **"Epidermal growth factor receptor erbB1 inhibitor"**，action_type = INHIBITOR，target = **CHEMBL203（EGFR）**。
- 数据库参考：DailyMed 说明书、EuropePMC 24893891 / 25271963。✅ChEMBL(mechanism_refs)
- 公司官网描述可作 🔍web 补充（AstraZeneca 产品页）。

## 4. 最高临床阶段 / 时间线（按适应症 · 🚧 G2 pivotal）

> ⚠️ 重要口径：CT.gov 计算出的"最高 phase"是**临床试验阶段**，**不等于上市**。
> Osimertinib 在美/中**均已上市**（美 NDA208065，2015 起；中 泰瑞沙，2017 起）。CT.gov 中 PHASE4 = 上市后试验。
> ✅ClinicalTrials.gov 统计（300/380 条）：🇺🇸 US n=110、最高 PHASE3；🇨🇳 China n=115、最高 PHASE4。

Osimertinib 适应症本质上是 **单一疾病（EGFR 突变 NSCLC）下的多个治疗线/分期**（284/300 条试验为 NSCLC/EGFR/肺癌）。
按"适应症（治疗设置）"拆分如下；**pivotal NCT 全部为 🔴 候选，须以 FDA 说明书 *Clinical Studies* 段 / CDE 上市依据核对**：

| # | 适应症（治疗设置） | 阶段（美/中） | pivotal 试验（🔴 候选，待人工核对）| 关键时间线 | 徽标 |
|---|------|------|------|------|------|
| A | **1L 晚期/转移性 EGFRm（Ex19del/L858R）单药** | 已上市（美 2018 / 中）| **FLAURA = NCT02296125**（III）| mPFS 18.9 vs 10.2 mo；mOS 38.6 vs 31.8 mo | 🔴 + 🔍web([targetedonc](https://www.targetedonc.com/)) |
| B | **1L 晚期 + 含铂化疗（培美曲塞）** | 已上市（美 2024-02）| **FLAURA2 = NCT04035486**（III）| 美 FDA 2024-02 批准（[FDA](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-osimertinib-chemotherapy-egfr-mutated-non-small-cell-lung-cancer)）| 🔴 + 🔍web |
| C | **2L T790M+（既往 EGFR-TKI 进展后）** | 已上市（美 2015 加速→2017 完全）| **AURA3 = NCT02151981**（III）| 对比化疗 PFS 获益 | 🔴 + 🔍web |
| D | **辅助治疗（完整切除 IB–IIIA EGFRm）** | 已上市（美 2020-12）| **ADAURA = NCT02511106**（III）| DFS 与 OS 均显著获益 | 🔴 + 🔍web |
| E | **III 期不可切除、放化疗后维持** | 已上市（美 2024-09 / 中 2024-12）| **LAURA = NCT03521154**（III）| 美 2024-09 批准（[AZ](https://www.astrazeneca.com/media-centre/press-releases/2024/tagrisso-us-approval-in-unresectable-lung-cancer.html)）| 🔴 + 🔍web |
| F | （在研）联合 savolitinib 治 MET 扩增耐药 | 中 2025-06 获批联合疗法 | SACHI / SAVANNAH 等 | 🔴 G5 + 🔍web([az-cn](https://www.astrazeneca.com/content/az-cn-zh/media/press-releases/2025/06-30-01.html)) |
| G | （在研/探索）CNS/脑转移、新辅助、ADC 联合等 | I–II | 多个研究者发起试验 | 起止见 CT.gov | ✅ClinicalTrials.gov |

- 时间线节点（开始/主要完成/完成日期）可逐 NCT 从脚本 `studies[].startDate/primaryCompletionDate/completionDate` 取。✅ClinicalTrials.gov
- ⚠️ 试验→适应症映射为自由文本、很脏；上表分组为人工归类，个别试验可能跨设置 → 不确定处标 🔴。
- 🇨🇳 中国侧各适应症的**正式批准时间/上市依据试验**应到 chinadrugtrials.org.cn + NMPA 核对（🔴 G5；本次脚本未抓中国库）。

## 5. 简介（含销售成绩 · 🚧 G4）
- TAGRISSO/泰瑞沙是 AstraZeneca 的第三代 EGFR-TKI，EGFR 突变 NSCLC 全线（1L、2L、辅助、III 期维持）旗舰产品，
  入脑活性较好。🔍web（AstraZeneca 产品页）
- **销售额（🔴 + 🚧 G4）**：2024 全年 Tagrisso 收入 **约 $6.6B（66 亿美元）**。
  来源：🔍web AstraZeneca FY2024 业绩公告 PDF（[astrazeneca.com FY2024 results](https://www.astrazeneca.com/content/dam/az/PDF/2024/fy/Full-year-and-Q4-2024-results-announcement.pdf)）。
  ⚠️ 具体数字/同比需以**年报原文页码**复核；季度/地区拆分未取 → 余者 ❓N/A。

## 6. LOE（专利/独占到期）— 美国 + 中国（整项 🔴 · 🚧 G3）

> ❗ 无"LOE=某日"现成字段，以下为**依据推算**，必须人工到官方库核对。

- **🇺🇸 美国（🔴 + ⚠️ 二手源）**：预计最早仿制进入 **≈ 2032-07-25**（部分来源称 2032-08-08）。
  依据：化合物专利 **US 9,732,058**（drug substance + product），另有报道称共 **17 项美国专利 + 4 项 FDA 独占期**，已有 **1 项 ANDA 暂定批准(tentative)**。
  来源：🔍web drugpatentwatch / pharmacompass / pharsight（**均为二手聚合站，⚠️ 须到 FDA Orange Book 原始记录核对**：https://www.accessdata.fda.gov/scripts/cder/ob/）。
- **🇨🇳 中国（🔴 G5）**：化合物专利约 **2032-07-25 到期**（与美国一致，多家中文医药媒体口径）。🔍web([摩熵医药](https://www.pharnexcloud.com/zixun/sx_7174)) ⚠️
  无 Orange Book 等价干净库 → 须到中国上市药品专利信息登记平台 / 行业数据库逐项核（https://zldj.cnipa.gov.cn/）。
- 生物药独占（Purple Book）：N/A（本品为小分子）。

## 7. 是否已有仿制药上市 — 美国 + 中国

| 地区 | 结论 | 依据 | 徽标 |
|------|------|------|------|
| 🇺🇸 美国 | **否（尚无可售仿制）**；仅有 ANDA *暂定批准(tentative)*，需待 2032 专利/独占放开 | 脚本 `openfda.drugsfda.has_anda_generic = false`、`ndc.marketing_categories` 仅 NDA/原料药，无 ANDA | ✅openFDA + 🔍web(⚠️ tentative ANDA 来自二手源) |
| 🇨🇳 中国 | **已获批但尚不能合法销售**：江苏万邦生化（复星医药子公司）**首仿 + 首家过评**（NMPA 2023-10-27 批准），**但原研化合物专利 2032-07-25 前不能上市销售** | 🔍web([医药魔方](https://bydrug.pharmcube.com/news/detail/cb1924d7e63f11ffac4687f4da1be686)、[摩熵医药](https://www.pharnexcloud.com/zixun/sd_7227)) | 🔴 G5 ⚠️（须 NMPA 批件核对） |

> 💡 这条最能体现工具价值：美国 `has_anda_generic=false` 是 ✅ 硬信号；
> 中国"批了但不能卖"是 🔴 脏信息，必须人工到 NMPA 核对批件号与是否专利链限制。

## 8. 同类药品（各列几个，不展开）

- **同 MoA/靶点（EGFR-TKI；target CHEMBL203）**：
  - 三代：Lazertinib（拉泽替尼，CHEMBL）、Almonertinib/阿美替尼、Furmonertinib/伏美替尼、Befotertinib/贝福替尼。
  - 一/二代：Gefitinib、Erlotinib、Afatinib、Dacomitinib。
  - 可信度：靶点同一性 ✅ChEMBL(target)；具体品种归类 🔍web ⚠️。
- **同适应症（EGFR+ NSCLC）竞品/在研**：Amivantamab（EGFR×MET 双抗）、各类 ADC（如 Dato-DXd、BL-B01D1）、Ivonescimab（依沃西）等。
  来源：CT.gov 近期试验对照臂 ✅ClinicalTrials.gov + 🔍web ⚠️。

## 9. 核心优势（AI 总结 · 整节 🔴 · 跨试验比较不严谨）

> 🔴 以下为 AI 基于公开信息的方向性归纳，**跨试验比较在统计上不严谨，仅供参考，须领域专家复核**。每条尽量附来源。

- **vs 一/二代 EGFR-TKI**：覆盖 T790M 耐药、入脑活性更好、野生型 EGFR 相关毒性更低；1L 头对头 FLAURA 显示 PFS/OS 获益。🔍web([targetedonc](https://www.targetedonc.com/)) 🔴
- **vs 同代三代 TKI（阿美/伏美/拉泽等）**：先发 + 适应症最全（唯一覆盖辅助 ADAURA、III 期 LAURA、1L+化疗 FLAURA2 的全线布局），证据链与可及性领先；但国产三代在中国有价格/医保优势。🔍web 🔴 ⚠️
- **同适应症（vs 双抗/ADC 新机制）**：作为口服单药基石地位稳固，但面临 amivantamab 联合、ADC 等新方案在耐药后线的竞争。🔍web 🔴 ⚠️

---

## 🔴 需人工核对清单（本工具最关键产出）

| # | 字段 | 当前值 / 状态 | 为什么要核 | 建议去哪个官方源核 |
|---|------|--------------|-----------|------------------|
| 1 | 步4 各适应症 **pivotal NCT** | FLAURA NCT02296125 / FLAURA2 NCT04035486 / AURA3 NCT02151981 / ADAURA NCT02511106 / LAURA NCT03521154（🔴 候选）| CT.gov 无 "pivotal" 字段；上市依据须从说明书反查 | FDA 说明书 *Clinical Studies* 段；CDE 上市依据 |
| 2 | 步4 试验→适应症归类 | 人工归类，个别可能跨设置 | 映射为自由文本、脏 | 逐 NCT 读 CT.gov + 说明书 |
| 3 | 步5 **2024 销售额** | ≈ $6.6B（🔴）| 财报级、易幻觉，未核页码 | AstraZeneca FY2024 年报/20-F 原文 |
| 4 | 步6 **美国 LOE** | ≈ 2032-07-25（US 9,732,058）（🔴⚠️ 二手源）| 需综合专利+独占期；来源为聚合站 | FDA Orange Book 原始记录 |
| 5 | 步6 **中国 LOE** | ≈ 2032-07-25（🔴⚠️）| 无干净库，媒体口径 | 中国上市药品专利信息登记平台 / NMPA |
| 6 | 步7 **美国仿制** | 否（仅 tentative ANDA）（✅否定 + ⚠️tentative）| tentative 信息来自二手源 | Orange Book / Paragraph IV 列表 |
| 7 | 步7 **中国仿制** | 万邦首仿已批但 2032 前不能卖（🔴）| 无干净 API，"批≠可售" | NMPA 批件库 / CDE 一致性评价 |
| 8 | 步2 **中国 MAH** | 阿斯利康制药有限公司（🔴 G5）| chinadrugtrials/NMPA 无 API | NMPA 数据库 |
| 9 | 步4 **中国各适应症批准时间/上市依据** | 部分见新闻稿（🔴 G5）| 脚本未抓中国库 | chinadrugtrials.org.cn + NMPA |
| 10 | 步8 同类药品归类 | 列表（⚠️）| 靶点同一性 ✅，品种归类弱 | ChEMBL target + 专业综述 |
| 11 | 步9 **核心优势全节** | AI 主观（🔴）| 跨试验比较不严谨 | 领域专家复核 |
| 12 | 任何 ❓N/A | 销售季度/地区拆分、中国库未抓项 | 显式列出查过的源 | 见各条 |

---
*脚本确定性来源快照：PubChem ✅ / ChEMBL ✅ / ClinicalTrials.gov ✅（300 of 380）/ openFDA ✅（NDA208065, 2015, has_anda_generic=false）。中国侧 + LOE 全程 web + 人工。*
