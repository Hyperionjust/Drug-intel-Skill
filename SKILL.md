---
name: drug-intel
description: >-
  药物研发竞争情报工具（仅美国 + 中国两地）。当用户说「查一下 X 药 / 帮我做 X 的药物情报 /
  X 的竞品分析 / X 的临床进展、厂家、MoA、专利到期(LOE)、是否有仿制药、同类药、核心优势」时使用。
  解析分子身份后，调用 scripts/fetch_drug_data.py 抓取确定性数据源（PubChem / ChEMBL /
  ClinicalTrials.gov / openFDA），再叠加 web 检索与人工确认，产出每个字段都带来源徽标、
  并在末尾汇总「🔴 需人工核对清单」的研发情报报告。Use for drug / pharma competitive
  intelligence, clinical-stage / manufacturer / mechanism / LOE / generics lookups.
---

# drug-intel — 药物研发竞争情报（美国 + 中国）

这是一套**运行时流程**。当有人说「查一下 X 药」时，你（Claude）按本文件从头到尾执行。
本工具只看 **美国 + 中国** 两个地区，其它地区不展开。

> ⚠️ 免责：本工具产出**仅供研发情报参考，非医疗建议、非投资建议**。所有高幻觉字段必须带徽标并经人工复核。

---

## 1. 最高优先级规则：全局来源标注（badges）

**报告里每一个字段都必须带来源徽标。** 「所有高幻觉区」和「判定为找不到的区域」一律**显式标注**，
绝不静默省略、绝不无来源直接给结论。

| 徽标 | 含义 | 用法 |
|------|------|------|
| ✅`<数据库名>` | 权威数据库可核实 | 例：✅PubChem、✅ChEMBL、✅ClinicalTrials.gov、✅openFDA。必须能在该库查到 |
| 🔍web | 联网检索到的 | **必须附 URL**。例：🔍web([astrazeneca.com/...](#)) |
| ⚠️ | 来源存疑 / 单一弱来源 | 建议人工确认；常见于"机构新闻稿"级来源 |
| 🔴 | 高幻觉区 或 必经人工确认 | **绝不允许无来源直接给结论**。即使查到也要标，并说明不确定性来源 |
| ❓N/A — 未找到 | 检索过但确实没找到 | **必须写明查过哪些源**。这本身也要显式标出，不能省略 |

**来源优先级（一律遵守）：** 公司官网 > FDA 与 CDE/NMPA 官网 > 权威医药媒体/数据库 > 其他。
查不到就写 `❓N/A` 并注明查过哪些源。**绝不编造事实、数字或来源。**

### 1.1 强制 🔴 的字段（不管查没查到，都标 🔴 并解释不确定性来源）

1. 上市所依据的**关键(pivotal)试验 NCT/CTR 号** —— CT.gov 无 "pivotal" 字段，需从 FDA 说明书
   *Clinical Studies* 段 / CDE 上市依据反查。
2. **任何药物销售额数字** —— 只在公司财报/年报，非产品页，且只有大品种单独披露。
3. **第 9 步核心优势**（AI 主观对比）—— 最主观高幻觉区。
4. **LOE 日期（中美）** —— 无现成 "LOE=某日" 字段，需综合专利+独占期推算。
5. **中国侧的任何审批/上市/仿制信息** —— 无干净 API，天然低可信。

---

## 2. 暂停门 (Pause Gates) — 必经人工确认后再继续

为防止错误向下游传播，**G0–G5 全部为默认硬停**：到达时**停下来、把该门的中间结论给用户、等确认后再继续**
（不是仅打徽标）。**唯一例外**：用户开场明确说「全部一次跑完别停」时，整批降级为"高亮 🔴 + 写进核对清单"（见文末实操）。

| 门 | 位置 | 默认硬停 — 为什么必须停 |
|----|------|------|
| 🚧 **G0 身份门** | 开场 A（分子消歧） | **硬停**：实体错 = 整篇报告全错。多候选必须让用户选定再跑 |
| 🚧 **G1 口径门** | 开场 B（阶段口径） | **硬停**：决定全文结构。先确认再继续 |
| 🚧 **G2 pivotal 门** | 第 4 步（上市依据 NCT/CTR） | **硬停**：喂给 LOE、说明书声明；映射极脏。给候选 + 来源，等用户拍板再继续 |
| 🚧 **G3 LOE 门** | 第 6 步（中美 LOE） | **硬停**：业务影响大、需推算。给"日期+依据+来源"，等用户确认推算逻辑再继续 |
| 🚧 **G4 销售额门** | 第 5 步（销售数字） | **硬停**：高幻觉高影响。给"数字+财报出处"，未取到则 ❓N/A，等用户确认再继续 |
| 🚧 **G5 中国门** | 第 4/6/7 步中国侧任何审批/上市/仿制结论 | **硬停**：无干净源。每条都等用户到官方站核对后再定稿 |

> 第 9 步核心优势虽是 🔴，但它是最后一步且已显式标注"AI 主观、跨试验比较不严谨"，
> 默认**重度打标 + 进核对清单即可，不设硬停**（除非用户要求逐条确认）。

**实操（默认）**：到达任一暂停门时，输出该门已得到的中间结论 + 候选/依据，然后问用户「确认/修正后我继续」，
**绝不**一口气把整篇跑完。多个门可在同一处一并提请确认（如 G0+G1 开场一起问），但未得确认不得跨过该门继续。

**实操（例外·一次跑完）**：仅当用户开场明确说「全部一次跑完别停 / 别问直接出」时，把 G2–G5（G0/G1 仍建议至少复述确认）
**降级为"高亮 🔴 + 写进核对清单"**，并在报告顶部显著声明"⚠️ 已按用户要求跳过暂停门，以下 🔴 项均未经确认"。

---

## 3. 中国侧专用来源（顺序）

中国临床/审批信息优先用官方源，按序：

1. **药物临床试验登记与信息公示平台** —— https://www.chinadrugtrials.org.cn/index.html （CDE 官方，**首选**）
2. **NMPA / CDE 官网** —— 审批、上市、一致性评价：https://www.nmpa.gov.cn/ ， https://www.cde.org.cn/
3. **权威医药媒体**（如药智、insight 数据库报道等）

> ⚠️ `chinadrugtrials.org.cn` **无公开 API、且为动态加载**，web 抓取可能不稳定。
> 取到 → 标 🔍web(URL)；取不到 → 标 `❓N/A` 并**提示用户手动到该站检索**（给出站点链接）。
> **中国侧整体默认高人工介入**，所有中国侧结论默认走 🔴 / G5 暂停门。

---

## 4. 开场确认（只问一次，再开跑）

收到「查 X 药」后，**先把脚本跑起来**（见第 5 节）拿到 `identity_rollup`，然后**一次性**问清两件事：

**A. 分子身份消歧（🚧 G0）**
用户输入可能是分子名 / 中文名 / 实验代号 / 商品名。解析出唯一实体：
INN、PubChem CID、ChEMBL ID、别名、盐型/游离碱。
- 用脚本的 `identity_rollup`（resolved_names / pubchem_cid / chembl_ids / research_codes / brand_names）+
  `pubchem.synonyms` 给出候选。
- **多候选 → 列出让用户选，确认后再继续。** 单一明确候选也复述一遍请用户确认。

**B. 阶段口径（🚧 G1）**
问用户要：
- 「**全局最远**」：所有适应症里走得最远的那个阶段；还是
- 「**按适应症逐个列**」：每个适应症分别给阶段 + 时间线。

> 用 `AskUserQuestion` 同时问 A、B 最干净。两问都确认后才进入九步工作流。

---

## 5. 数据脚本（确定性源，先跑它）

```bash
python scripts/fetch_drug_data.py "<药名或代号>"
# 可选： --max-studies 250   --no-studies-list   --compact
```

- 纯 stdlib（urllib），无需 pip。返回合并 JSON 到 stdout。
- 覆盖**有干净 API 的确定性源**，这些字段可直接打 ✅：

| JSON 路径 | 来源 | 喂给哪步 | 徽标 |
|-----------|------|---------|------|
| `deterministic_sources.pubchem` | PubChem | 步1 身份/结构/式/SMILES/PNG | ✅PubChem |
| `deterministic_sources.chembl.molecules / best_match` | ChEMBL | 步1 ChEMBL ID、max_phase | ✅ChEMBL |
| `deterministic_sources.chembl.mechanisms` | ChEMBL | 步3 MoA（数据库级） | ✅ChEMBL |
| `deterministic_sources.clinicaltrials_gov.us / china / phase_distribution / recent_trials / studies` | CT.gov v2 | 步4 阶段/时间线/计数 | ✅ClinicalTrials.gov |
| `deterministic_sources.openfda.drugsfda` | openFDA | 步2 厂家(US)、步5 批准年、步7 ANDA信号 | ✅openFDA |
| `deterministic_sources.openfda.ndc` | openFDA | 步7 在售/仿制类别 | ✅openFDA |

- **关键约定**：任何源失败/查无 → 该源在 JSON 里是 `null`，`source_status` 写明原因。
  **`null` 永远不等于"药不存在"**。早期代号在 openFDA 常查不到属正常（脚本会返回 `openfda: no_data`）。
- `web_and_manual.*` 字段脚本一律返回 `null` + 该去哪个官方站的 URL —— 这些走 web + 人工（见各步）：
  中国临床(chinadrugtrials)、美国 LOE(Orange/Purple Book)、中国专利、中国仿制。

> CT.gov 的 `us.highest_phase` 是**临床试验阶段**，**不等于已上市**。是否上市看 openFDA（美国）/ NMPA（中国）。
> 脚本统计是基于已抓取的 N 条（`fetched`/`total_matching`）；需要更全就调大 `--max-studies`。

---

## 6. 工作流九步（+ LOE + 仿制）

> 每步产出都要带徽标。能用脚本 ✅ 的优先 ✅；脚本没有的去 web（🔍 附 URL）；中国侧/LOE/销售额/pivotal 走 🔴 + 暂停门。

### 步骤 1 · 分子名确认
- 中英文互校。脚本已在 PubChem / ChEMBL 命中；另在 **openFDA、CDE/NMPA、ClinicalTrials.gov、
  chinadrugtrials.org.cn** 检索该名称/代号并抓取命中记录。
- 输出：INN、中文名、CID、ChEMBL ID、盐型/游离碱、别名、分子式、结构图 PNG URL。
- 早期代号在 FDA 查不到 → 标 `❓N/A — 未找到（已查 openFDA drugsfda/ndc）`，不算异常。

### 步骤 2 · 厂家确认（区分三种角色）
明确区分 **原研 / 当前权利人(license holder) / 上市许可持有人(MAH)**。按序溯源：
1. 公司官方公告（最高，🔍web 附 URL） →
2. ClinicalTrials.gov / CDE 试验 `sponsor` 字段（✅；脚本 `leadSponsor`、`openfda.drugsfda.sponsor_name`） →
3. 大型机构新闻稿（**标 ⚠️ 需人工确认**）。
- **分别给出美国、中国各自的权利人 / MAH**（不再统计"几家"）。
- 中国侧 MAH → 🔴 / G5（chinadrugtrials/NMPA 核对）。

### 步骤 3 · MoA（作用机制）
优先级：
1. 药企官网（🔍web 附 URL） →
2. **ChEMBL `mechanism_of_action`**（数据库级，✅ChEMBL；脚本 `chembl.mechanisms`，含 target_chembl_id） →
3. 临床试验 info 描述（标 NCT 号） →
4. 网络资源（**标 ⚠️**）。

### 步骤 4 · 最高临床阶段 / 时间线（🚧 G2）
依开场 B 的口径：
- **「全局最远」**：直接定位最晚阶段（脚本 `clinicaltrials_gov.overall_highest_phase` + openFDA/NMPA 上市状态）。
- **「按适应症」**：
  1. 先确认有多少适应症在研/已上市（从 `studies[].conditions` 聚类 + web 校正）。
  2. 对每个适应症，抓 **ClinicalTrials.gov（脚本 studies）+ chinadrugtrials.org.cn/CDE（🔍web/❓N/A）** 的相关试验，
     按 **上市 > III > II > I** 排序。
  3. 若已上市，标注其 **pivotal 试验 NCT/CTR 号 → 🔴 + 🚧 G2**：CT.gov 无 "pivotal" 字段，
     需从 **FDA 说明书 Clinical Studies 段 / CDE 上市依据**读取，**必经人工确认**。
  4. 为每个适应症各阶段编写**时间线**（开始 / 主要完成 / 完成 日期；脚本 `startDate / primaryCompletionDate /
     completionDate`）。
- ⚠️ **试验→适应症映射是自由文本、很脏**；任何时间线节点不确定就标 🔴。
- 中国侧阶段/试验 → 🔴 / G5。

### 步骤 5 · 简介（🚧 G4 销售额）
- 若已上市：摘公司官网主要介绍（🔍web）。
- **销售成绩 → 🔴 + 🚧 G4**：销售数字只在公司**财报/年报**，非产品页，且只有大品种单独披露。
  给"数字 + 财报出处(年份/季度/页)"；取不到写 `❓N/A — 未找到（已查 XX 年报）`。**绝不估算/编造数字。**

### 步骤 6 · LOE（专利/独占到期）— 美国 + 中国（整项强制 🔴 + 🚧 G3）
- **美国**：查 **FDA Orange Book**（小分子：专利 + 独占期）/ **Purple Book**（生物药）。
  无现成 "LOE=某日" 字段 → 综合**最晚放开仿制的专利 + 独占期**判断。
  产出：**"预计 LOE + 依据的专利号/独占类型 + 来源 URL"**（🔍web + 🔴）。
- **中国**：无 Orange Book 等价干净库 → 中国上市药品专利信息登记平台 / 行业数据库 / 新闻**推算**（🔴 / G5）。
- **整项强制 🔴**：**必须列出依据，绝不只给一个孤立日期**；取不到写 `❓N/A` 并说明为何难取。

### 步骤 7 · 是否已有仿制药上市 — 美国 + 中国
- **美国**：openFDA / Orange Book 是否有 **ANDA（仿制）获批** → **是/否 + 首个获批年（若有）**。
  脚本信号：`openfda.drugsfda.has_anda_generic`、`openfda.ndc.marketing_categories.ANDA`（✅openFDA）。
- **中国**：NMPA 是否有**同通用名仿制批文 / 通过一致性评价**记录 → **是/否**（🔴 / G5，需人工确认）。
- 输出**布尔结论 + 来源**；查不到写 `❓N/A`。

### 步骤 8 · 同类药品
基于上面检索结果，分两组各列几个名字即可（**不展开**）：
- **同 MoA/靶点** 的药（用 ChEMBL 靶点 `target_chembl_id` / 已知药物类别，标可信度）；
- **同适应症** 竞品（从 CT.gov `conditions` / web）。
- 每组标可信度徽标。

### 步骤 9 · 核心优势（AI 总结 · 整节 🔴）
对比 **同类型药品** 与 **同适应症药品** 各自的核心优势：
- **最主观高幻觉区**：每条带来源（🔍web / ✅）。
- 加免责：**"跨试验比较在统计上不严谨，仅供方向性参考"**。
- **整节标 🔴 需专家复核**（默认不暂停，但必入核对清单）。

---

## 7. 报告输出模板

> 顶部固定放免责 + 身份卡 + 徽标说明；每步按上面顺序；**末尾必出核对清单**。

```markdown
# 药物情报报告：<INN / 商品名>（美国 + 中国）
> 仅供研发情报参考，非医疗/投资建议。生成时间：<UTC>。口径：<全局最远 / 按适应症>。
> 徽标：✅库 可核实 ｜ 🔍web 附URL ｜ ⚠️ 存疑 ｜ 🔴 高幻觉/必核 ｜ ❓N/A 查过未找到

## 0. 身份卡
- INN / 中文名 / 代号 / 商品名 / CID / ChEMBL ID / 盐型 / 分子式 / 结构图  …各带徽标

## 1. 分子名确认
## 2. 厂家（🇺🇸 原研/权利人/MAH ｜ 🇨🇳 原研/权利人/MAH）
## 3. MoA
## 4. 最高临床阶段 / 时间线（按口径；pivotal NCT/CTR 🔴）
## 5. 简介（含销售成绩 🔴）
## 6. LOE（🇺🇸 / 🇨🇳，整项 🔴：日期 + 依据 + 来源）
## 7. 仿制药上市？（🇺🇸 是/否+年 ｜ 🇨🇳 是/否 🔴）
## 8. 同类药品（同MoA / 同适应症）
## 9. 核心优势（AI 总结 🔴 + 跨试验不严谨免责）

## 🔴 需人工核对清单   ← 本工具最关键产出
```

---

## 8. 末尾「🔴 需人工核对清单」生成规则（最关键产出）

报告末尾**必须**生成一节 `## 🔴 需人工核对清单`，把全篇**所有 🔴 / ⚠️ / ❓N/A 汇总成 checklist**。
每条包含三栏：

```markdown
| # | 字段 | 当前值/状态 | 为什么要核 | 建议去哪个官方源核 |
|---|------|------------|-----------|------------------|
| 1 | 步4 pivotal 试验 NCT | <候选或❓N/A> | CT.gov 无pivotal字段，映射脏 | FDA 说明书 Clinical Studies / CDE 上市依据 |
| 2 | 步5 年销售额 | <数字或❓N/A> | 财报级、易幻觉 | 公司年报/季报 |
| 3 | 步6 美国 LOE | <日期+依据或❓N/A> | 需综合专利+独占期推算 | FDA Orange/Purple Book |
| 4 | 步6 中国 LOE | … | 无干净库 | 中国专利登记平台/行业库 |
| 5 | 步7 中国仿制 | … | 无干净API | NMPA / CDE |
| 6 | 步2/4 中国MAH/试验 | … | chinadrugtrials动态、无API | chinadrugtrials.org.cn / NMPA |
| 7 | 步9 核心优势 | AI主观 | 跨试验比较不严谨 | 领域专家复核 |
| … | 任何 ❓N/A | 查过未找到 | 显式列出 | 列出已查的源 |
```

清单要把**所有**带 🔴/⚠️/❓N/A 的字段都收进来（含中国侧每一项），不得遗漏。

---

## 9. 自动化可靠性（执行时心里有数）

- **稳（脚本 ✅，可靠自动化）**：分子身份/结构（PubChem）、ChEMBL ID 与 MoA、CT.gov 阶段/计数/时间线、
  美国 openFDA 批准与 ANDA 信号。这些直接打 ✅。
- **每次都靠 web、可能不稳**：公司官网原文、销售额(财报)、pivotal NCT/CTR、美国 LOE(Orange/Purple Book)、
  **整个中国侧**（chinadrugtrials 动态无API、NMPA 审批/仿制、中国专利/LOE）。这些标 🔍web/🔴/❓N/A，走暂停门。
- 失败处理：脚本任一源 `null` → 当作"该源没查到"，继续其它源与 web；**绝不**因一源失败就下"药不存在"。

> 记住：本工具的价值不在"给一个漂亮答案"，而在**诚实地标注每个字段的可信度**，
> 并把不确定的东西清清楚楚交到人手上核对。宁可 `❓N/A` 也不编。
