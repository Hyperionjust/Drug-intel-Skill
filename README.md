# drug-intel · 药物研发竞争情报

一个 Claude 技能（Skill）。你说一句「**查一下 X 药**」，它就帮你把这只药在 **美国 + 中国** 两地的情况
整理成一份报告：临床进展、厂家、作用机制、专利到期、有没有仿制药、同类药、核心优势。

它和普通问答最大的不同是：**报告里每一个字段都标了来源**，并在结尾附一张
**「🔴 需人工核对清单」**——把所有"容易编、最好别全信"的地方挑出来，告诉你该去哪个官网核对。
目的不是给一个看着漂亮的答案，而是给一个**你能放心引用的答案**。

> 仅供研发情报参考，**非医疗建议、非投资建议**。

> 🔰 **第一次用、或不太懂技术？** 先看 [`GETTING_STARTED.md`](GETTING_STARTED.md)（保姆级新手指南，含
> "怎么开联网、怎么放行网站、怎么发起查询、看懂徽标、出错怎么一键修"）。

**这一版新增**：① 官方源（政府/监管/企业官网）对**客观事实**可标**最高可信 🏛️官方**，但销售额与主观对比仍强制 🔴；
② 暂停门的提问全部改成大白话；③ 除了 chat 文字报告，还能出 **HTML / PDF 可视化报告**（时间线 + 适应症矩阵 + 销售趋势 + 红色核对清单）。

---

## 它能帮你查什么

说出药名后，你会拿到这些内容（每条都带来源徽标）：

- **分子身份** —— 先把你给的名字（中文名 / 商品名 / 研究代号都行）对到唯一的分子
- **厂家** —— 区分原研、当前权利人、上市许可持有人，美中分开
- **作用机制（MoA）** 和 **靶点**
- **临床进展 / 时间线** —— 可按"走得最远的阶段"或"按适应症逐个列"
- **专利与独占到期（LOE）** —— 美国、中国分别给"预计日期 + 依据"
- **有没有仿制药/生物类似药上市** —— 美国、中国分别给是 / 否
- **同类药** 与 **核心优势对比**

> 想看成品长什么样：
> - 文字版：[`examples/osimertinib-by-indication-sample.md`](examples/osimertinib-by-indication-sample.md)（奥希替尼）
> - 可视化版：[`examples/enhertu-report.html`](examples/enhertu-report.html)（Enhertu，含时间线/适应症矩阵/销售趋势/红色清单）

---

## 怎么安装

### 方式一：桌面版一键上传（推荐）

1. 在项目根目录跑一次打包脚本，得到 `drug-intel.zip`：
   ```bash
   python build_skill.py
   ```
2. 打开 **Claude 桌面版 → 设置 / Customize → Skills → Upload skill**，选这个 `drug-intel.zip` 即可。
   （如果上传框只认 `.skill`，把文件名改成 `drug-intel.skill` 就行，格式完全一样。）

claude.ai 网页版的上传入口和格式相同。

### 方式二：放进 Claude Code 的 skills 目录

把整个 `drug-intel/` 文件夹放到下面任一位置，重启后即可被发现：

- 只在某个项目里用：`<你的项目>/.claude/skills/drug-intel/`
- 所有项目都能用：`~/.claude/skills/drug-intel/`
  （Windows 是 `%USERPROFILE%\.claude\skills\drug-intel\`）

---

## 怎么用

装好后，直接用大白话说就行，比如：

> 查一下 Enhertu
> 帮我做一下 trastuzumab deruxtecan 的竞品情报
> 优赫得的临床进展和专利到期帮我看看

**开跑前它会用大白话问你一两个小问题**（用正常聊天的口吻，不会甩术语）：

1. **"你要查的是不是这只药？"** 如果名字能对到好几个候选，它会列出来让你选。
2. **"想看最高进度，还是逐个适应症？"** 一句话给你最快进度，或按乳腺癌/胃癌/肺癌……分别列。
3. **"要不要一次写完？"** 边写边停下来问你，还是一口气出初稿、把要核对的地方都用红色集中标在最后。

报告生成过程中，遇到几个**高风险、容易出错的点**（分子身份、阶段、上市依据试验、专利到期、
销售额、所有中国侧结论），它默认会**停下来把中间结果给你、等你确认再继续**。
如果你赶时间，开头说一句「全部一次跑完别停」，它就不停了，但会在报告顶部明确标注"这些 🔴 项都没经过你确认"。

> 想要**能存档/发给同事的好看文档**？加一句「**给我出一份 HTML / PDF 的可视化报告**」，
> 它会画出带**时间线、适应症对照矩阵、销售趋势图、红色核对清单**的版本（见 `examples/enhertu-report.html`）。

---

## 报告里的徽标怎么读

| 徽标 | 意思 |
|------|------|
| 🏛️ 官方 | **最高可信**：来自政府/监管官网（FDA、NMPA、CDE）或企业官网的**客观事实**（批准日期、获批适应症、机制、专利号等）。⚠️ 只对"事实"生效 |
| ✅ `数据库名` | 权威数据库可核实（与 🏛️官方 同属最高一档）|
| 🔍 web | 联网搜到的（非官方/二手），会附上链接 |
| ⚠️ | 来源存疑，或只有单一弱来源，建议你再确认一下 |
| 🔴 | 高幻觉区 / 必须人工确认——**绝不会没来源就给结论** |
| ❓ N/A | 认真查过、确实没找到（会写明查了哪些源） |

> **关键边界**：销售额/财务数字、"哪个药更好"这类主观对比，**即使来自官网也仍标 🔴**——
> 官方源能让"事实"更可信，但不替"宣传/主观"背书。这正是本工具靠谱的地方。

报告**最后那张「🔴 需人工核对清单」是这个工具的重点产出**：它把全篇所有 🔴 / ⚠️ / ❓
汇总成一张表，逐项告诉你"为什么要核、去哪个官网核"。

几个**一定会标 🔴** 的字段：上市所依据的关键试验编号、任何销售额数字、专利到期（中美）、
核心优势对比、以及**中国侧的一切审批 / 上市 / 仿制信息**（中国这边没有干净的官方 API，天然要人工兜底）。

---

## 单独跑数据脚本（可选）

报告里"确定性、有现成 API"的那部分，是由 `scripts/fetch_drug_data.py` 抓的。
这个脚本**不依赖 Claude、纯标准库、不用装任何东西**，可以单独跑，吐出一份合并好的 JSON：

```bash
python scripts/fetch_drug_data.py "Osimertinib"
python scripts/fetch_drug_data.py "AZD9291" --max-studies 250
python scripts/fetch_drug_data.py "Tagrisso" --no-studies-list --compact
```

| 参数 | 说明 |
|------|------|
| 药名（必填） | 药名 / INN / 商品名 / 研究代号；含空格记得加引号 |
| `--max-studies N` | ClinicalTrials.gov 最多抓多少条试验（默认 200） |
| `--no-studies-list` | 只保留统计汇总，去掉逐条试验明细（输出更短） |
| `--compact` | 输出成单行 JSON |

**脚本能可靠拿到的**（报告里可直接打 ✅）：

- **PubChem** —— 名字→CID、分子式、SMILES、IUPAC 名、别名、结构图链接
- **ChEMBL** —— 分子检索、最高阶段、作用机制、靶点
- **ClinicalTrials.gov** —— 按药检索试验，并算出美 / 中各自的最高阶段、试验数、近期动态
- **openFDA** —— FDA 批准情况、厂家、最早批准年、有没有 ANDA（仿制药）信号

**脚本拿不到、要走联网 + 人工的**（会返回 `null` 并附上官网链接）：

- 中国临床试验（`chinadrugtrials.org.cn`，动态页、无公开 API）
- 美国 LOE（Orange Book / Purple Book，没有"到期=某天"这种现成字段，要自己推算）
- 中国专利 / 中国仿制（NMPA / CDE，没有干净 API）

> 一个重要约定：**某个源查不到 ≠ 这只药不存在**。研究代号（比如 AZD9291）在 openFDA 查不到是正常的；
> 生物药/ADC 在 PubChem 化合物库查不到也正常。任何一个源失败或查空，脚本都只把那个源记成 `null`、写明原因，绝不崩溃，也绝不当成"药不存在"。
> 如果**所有源都报 error**，多半是运行环境没放开联网域名 —— 见 `GETTING_STARTED.md`。

---

## 生成可视化报告（可选）

报告里的图（时间线 / 适应症矩阵 / 销售趋势 / 红色核对清单）由 `scripts/build_report.py` 渲染：
它读一份结构化 JSON（格式见 `templates/report_schema.json`），输出**自包含单文件 HTML**（无外部依赖、可离线打开、可"打印成 PDF"）。

```bash
# HTML（可在浏览器"打印→存为 PDF"）
python scripts/build_report.py examples/enhertu-data.json -o examples/enhertu-report.html
# Word 文档（同一份 JSON）
python scripts/build_report_docx.py examples/enhertu-data.json -o examples/enhertu-report.docx
```

三种格式（HTML / PDF / Word）内容一致，都是**完整文档**；所有引用链接统一汇总在报告最后的「参考来源」一节。

> 正常用的时候你**不用碰这个脚本**——直接对 Claude 说「出一份 HTML/PDF 报告」即可，它会自动填好 JSON 再调用它。

---

## 文件结构

```
drug-intel/
├── SKILL.md                          # 运行时流程：Claude 按它一步步执行（徽标规则 + 暂停门 + 九步工作流 + 输出模式分叉）
├── GETTING_STARTED.md                # 新手保姆级上手（联网开关 + 域名白名单 + 一键修复）  ← 第一次用看这个
├── scripts/
│   ├── fetch_drug_data.py            # 确定性数据采集器（纯标准库，无需 pip，永远第一步）
│   ├── build_report.py               # 可视化报告生成器（JSON -> 自包含 HTML，可打印成 PDF）
│   └── build_report_docx.py          # Word 版生成器（同一份 JSON -> 可编辑 .docx）
├── templates/
│   ├── report_schema.json            # 可视化报告的数据契约（build_report.py 的输入格式）
│   └── report_template.html          # 配色 / 组件骨架的设计参考
├── examples/
│   ├── osimertinib-by-indication-sample.md   # 文字版样例报告
│   ├── enhertu-data.json             # Enhertu 可视化报告的输入数据（已带徽标）
│   ├── enhertu-report.html           # 可视化报告样例（HTML，竖向时间线 + 矩阵 + 销售 + 红色清单 + 参考来源）
│   ├── enhertu-report.pdf             # 同一报告的 PDF
│   └── enhertu-report.docx            # 同一报告的 Word 版
└── README.md                         # 本文件
```

## 依赖

Python 3.8+（只用标准库，已在 3.14 验证）；以及能联网访问 PubChem / ChEMBL / ClinicalTrials.gov / openFDA。
`build_report.py` 同样只用标准库；转 PDF 可用浏览器打印或 `weasyprint`（可选）。
Word 版 `build_report_docx.py` 需要 `pip install python-docx`。
