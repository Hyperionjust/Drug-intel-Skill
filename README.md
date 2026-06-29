# drug-intel

药物研发竞争情报 Claude Code Skill —— **仅覆盖美国 + 中国**。

说「**查一下 X 药**」，Claude 就会解析分子身份、跑确定性数据脚本、叠加联网检索与人工确认，
产出一份**每个字段都带来源徽标**、并在末尾汇总 **「🔴 需人工核对清单」** 的研发情报报告。

> 仅供研发情报参考，**非医疗建议、非投资建议**。本工具的核心价值是诚实标注每个字段的可信度，
> 而不是给一个看起来漂亮、实则可能编造的答案。

---

## 文件结构

```
drug-intel/
├── SKILL.md                  # 运行时流程（Claude 按它执行）：徽标规则 + 暂停门 + 九步工作流 + 核对清单
├── scripts/
│   └── fetch_drug_data.py    # 确定性数据采集器（纯 stdlib，无需 pip）
└── README.md                 # 本文件
```

## 安装

把 `drug-intel/` 放到 Claude Code 的 skills 目录即可被发现：

- 项目级：`<repo>/.claude/skills/drug-intel/`
- 用户级：`~/.claude/skills/drug-intel/`（Windows：`%USERPROFILE%\.claude\skills\drug-intel\`）

之后在对话里说「查一下 Osimertinib」「帮我做 XX 的竞品情报」即可触发；
也可显式 `/drug-intel <药名>`。

## 直接跑数据脚本

脚本本身可独立运行（不依赖 Claude），返回合并 JSON：

```bash
python scripts/fetch_drug_data.py "Osimertinib"
python scripts/fetch_drug_data.py "AZD9291" --max-studies 250
python scripts/fetch_drug_data.py "Tagrisso" --no-studies-list --compact
```

| 参数 | 说明 |
|------|------|
| `name`（必填） | 药名 / INN / 商品名 / 研究代号（含空格请加引号） |
| `--max-studies N` | ClinicalTrials.gov 抓取上限（默认 200） |
| `--no-studies-list` | 只保留汇总，丢掉逐条 `studies` 数组（输出更短） |
| `--compact` | 单行 JSON |

### 脚本覆盖的确定性源（可直接打 ✅）

| 源 | 内容 | API |
|----|------|-----|
| **PubChem** PUG-REST | name→CID、分子式、SMILES、IUPAC、别名、结构图 PNG URL | ✅ 干净 |
| **ChEMBL** REST | molecule 搜索（chembl_id / pref_name / max_phase）、`mechanism_of_action` | ✅ 干净 |
| **ClinicalTrials.gov** v2 | 按 intervention 检索 → phases / status / country / 日期 / sponsor，并算出 **US/中国最高 phase + 计数 + 近期事件** | ✅ 干净 |
| **openFDA** | drugsfda + ndc → 批准、sponsor、**ANDA(仿制)信号**、最早批准年 | ✅ 干净 |

### 脚本**不**抓、走 web + 人工的区域（返回 `null` + 官方站 URL）

- 中国临床试验（`chinadrugtrials.org.cn`，动态、无公开 API）
- 美国 LOE（Orange Book / Purple Book，无 "LOE=日期" 字段，需推算）
- 中国专利 / 中国仿制（NMPA / CDE，无干净 API）

这些在 SKILL.md 里走联网检索 + 人工确认，并强制 🔴 / 暂停门。

### 健壮性约定

- 任一源失败或查无 → 该源返回 `null`，`source_status` 写明原因。
- **`null` 永不等于"药不存在"**。研究代号（如 AZD9291）在 openFDA 查不到属正常。
- 脚本永不因单源失败而崩溃；总是打印合法 JSON，正常退出。

## 徽标体系（详见 SKILL.md）

| 徽标 | 含义 |
|------|------|
| ✅`<库>` | 权威数据库可核实 |
| 🔍web | 联网检索（附 URL） |
| ⚠️ | 来源存疑 / 单一弱来源 |
| 🔴 | 高幻觉区 / 必经人工确认（绝不无来源给结论） |
| ❓N/A — 未找到 | 查过但确实没找到（写明查过哪些源） |

**强制 🔴 字段**：pivotal 试验 NCT/CTR、任何销售额、第 9 步核心优势、中美 LOE、中国侧一切审批/上市/仿制信息。

## 依赖

- Python 3.8+（仅标准库；已在 3.14 验证）。
- 联网访问 PubChem / EBI(ChEMBL) / ClinicalTrials.gov / openFDA。
