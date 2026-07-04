<div align="center">

![营销因果个性化 — Scientific Marketing](assets/hero.png)

# 营销因果个性化 · Scientific Marketing

### HTE / Uplift / Incrementality — 打包为 Claude Code skill

[![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-6E56CF)](https://claude.ai/code)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](#-依赖与示例)
[![References](https://img.shields.io/badge/references-19-44883e)](#-参考库)
[![CI](https://github.com/alexwang91/scientific-marketing-personalized-attribution-hte/actions/workflows/validate.yml/badge.svg)](https://github.com/alexwang91/scientific-marketing-personalized-attribution-hte/actions/workflows/validate.yml)
[![Scripts](https://img.shields.io/badge/scripts-6-blue)](#-脚本)
[![Provenance contract](https://img.shields.io/badge/numbers-sourced%20%C2%B7%20assumed%20%C2%B7%20derived%20%C2%B7%20missing-orange)](#-方法论立场)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

**传统个性化问「谁最可能买」。因果个性化问「我的动作让谁*多*买了」。**

τ(x) = E[Y(1) − Y(0) | X = x]

[快速开始](#-快速开始) · [这是什么](#-这是什么) · [工作原理](#-工作原理) · [参考库](#-参考库) · [方法论](#-方法论立场)

**English README** → [`README.md`](README.md)

</div>

---

## ✨ 这是什么

一个把营销因果推断**做成可执行决策流程**的知识库，打包为 Claude Code agent skill。不是一个模型，而是一套系统：

- **AI 负责生成** — 动作变体、从非结构化数据（评论/客服/销售记录）提取上下文、写实验文档、解释模型、监控漂移。
- **因果方法负责判断** — 动作是否有*增量*价值（τ(x)），而不是相关性。
- **制度负责兜底** — 实验优先、provenance 合约、对抗式评审、合规红线。

---

## 🖼 证明

脚本是跑通验证过的，不是伪代码。下图为 `scripts/qini_auuc.py` 的真实输出：

<div align="center">

![Qini / AUUC curve — scripts/qini_auuc.py 的真实输出](qini_curve.png)

*Qini 曲线：横轴 = 按预测 uplift 排序的触达比例，纵轴 = 累计增量。模型曲线与随机线之间的面积 = 模型创造的价值。*

</div>

---

## 🚀 快速开始

```bash
git clone https://github.com/alexwang91/scientific-marketing-personalized-attribution-hte.git
cd scientific-marketing-personalized-attribution-hte
```

Claude Code 会自动加载 `.claude/skills/` 下的 skill。问任何关于**营销增量、uplift、实验设计、发券策略、归因 vs 增量、线索路由**的问题即触发——包括大白话版的「这个客户该不该发优惠券」「我的广告到底有没有用」「谁该投、谁该跳过」。

**生成一份决策报告：**

```bash
cd .claude/skills/sm-causal-personalization/scripts
python generate_report.py --config ../examples/sample-sku-en-config.json --output report.html
python generate_report.py --config ../examples/sample-sku-en-config.json --validate-only   # 仅校验 provenance 合约
python generate_report.py --config ../examples/sample-sku-en-config.json --depth quick      # 高管速览：结论+单位经济+门控+证据
python generate_report.py --config ../examples/sample-sku-en-config.json --depth deep       # 完整报告 + 验证路线图（§18）
python generate_report.py --config ../examples/sample-sku-en-config.json --format dashboard --output dashboard.html            # 交互式决策看板
python generate_report.py --config ../examples/aurora-airpurifier-category-config.json --format dashboard --output portfolio-dashboard.html
python generate_report.py --config ../examples/aurora-airpurifier-category-config.json      # 类目货盘诊断（ref 17）
python generate_report.py --demo > demo.html                                               # 最小 schema 示例
python generate_report.py --demo --format dashboard > demo-dashboard.html                   # 最小看板示例
python generate_report.py --config c.json --embed-echarts echarts.min.js --output r.html   # 离线 HTML（图表库内嵌，不走 CDN）
```

报告分三档深度（`--depth`）：`quick` 只渲染决策关键章节；`standard`（默认）完整报告；`deep` 在完整报告后追加一张**验证路线图（§18）**——把未决评审挑战、缺失台账、测试预测合并为一张按「能否改变决策」排序的清单。只用配置里已有的数据，绝不新造数字。

当你想把同一套因果逻辑做成看板时，用 `--format dashboard`：KPI 条、单位经济卡片、渠道筛选、因果链路、热力图、treatment gates、evidence ledger 会被组织成一个可点击的 cockpit。输出仍然是单文件 HTML，内联 CSS/JS，不需要额外服务。

**跑核心脚本：**

```bash
python power_analysis.py    # uplift 实验功效：检测增量差异所需样本（≈ 标准 A/B 的 4×）
python qini_auuc.py         # Qini / AUUC + bootstrap CI + 分桶校准
python ope_estimators.py    # IPS / SNIPS / Doubly-Robust off-policy 评估 + support 检查
python hte_starter.py       # T / X / DR-learner 起手式（sklearn，可换 EconML / CausalML）
python policy_budget.py     # λ* 预算约束分配 + IPW 政策价值 + 利润-预算曲线
```

也可以整体装成 pip 包（`smcp`，附带 `sm-report` 命令行）：

```bash
pip install .               # 在仓库根目录执行
python -c "from smcp.policy_budget import allocate"
sm-report --demo > demo.html
```

---

## 🏗️ 工作原理

**四层生产架构：**

```
Layer 1 · 数据与实验资产    RCT 日志 + 倾向性 P(t|x) + GCG + 历史实验
                             （每个实验都是可复用的评估资产）
Layer 2 · 效应估计          τ̂(x) via DR-learner / Causal Forest / X-learner
                             （既校准又排序；收入用 ZILN 损失）
Layer 3 · 决策与分配        策略 π(x)：argmax + λ* 预算约束 + OPE 上线门
                             （大动作空间用 MIPS / OffCEM）
Layer 4 · 生成与服务（可选） LLM embedding 作特征（不进决策回路）；
                             文案个性化服务层
```

**成熟度三级，禁止跳级：**

| Level | 内容 | 多数团队 |
|-------|------|---------|
| **L1** | GCG + 回溯式 uplift 分析 | 所有团队的起点 |
| **L2** | 离线策略学习 + OPE 验证 + 周期重训 | **应长期停在这里** |
| **L3** | 上下文 bandit 在线学习 | 仅当动作多、环境变化快时 |

**产品×国家流水线**（ref 13）：Stage 0 本地市场情报 → 证据 → 单位经济 → 渠道筛（可在此终止）→ 维度 → 评审 → 测试 → 渲染报告。

---

## 📚 参考库

每个 reference 固定模板：**何时用 → 决策树 → 最小必要数学 → 分步操作 → 常见死法 → 验收清单 → 文献**。决策指南，不是教科书。

<details>
<summary><b>展开全部 19 篇</b></summary>

**研究与立项**
| Ref | 主题 |
|-----|------|
| `00` local-market-intelligence | 动态市场扫描：7 轴定位 → 迁移假设台账 → 差异化假设 → 排序 → 再编排 |
| `00b` customer-voice-competitor-scan | 按互动量挖真人评论/竞品，填充 Push/Pull/Habit/Anxiety 四力与候选维度（voice = Hypothesis 级，只生成「要测什么」） |
| `01` problem-framing | 利润口径；attribution × incrementality × MMM 三角；WTP → 折扣窗口 |

**核心因果链**
| Ref | 主题 |
|-----|------|
| `02` treatment-design | 动作库、treatment card、四力机制、LLM 变体爆炸的应对、archetype 优先的 KOL 评分 |
| `03` experiments | 识别阶梯、GCG 制度、HTE 功效、倾向性日志、假设→验证台账 |
| `04` hte-estimation | learner 选型默认路径；Qini/AUUC 验证三件套 |
| `05` uplift-segmentation | 四象限（沟通用）、Ascarza 教训、sleeping dogs |
| `06` policy-nbt | 策略价值、预算约束 λ*、OPE 上线流程 |
| `07` bandits-online | L3 准入四问、Thompson Sampling、漂移与回路 |
| `08` long-term-value | surrogate index、pull-forward、长期 holdout |

**治理与落地**
| Ref | 主题 |
|-----|------|
| `09` governance | 特征四问、红队清单、anti-persona、AI 角色红线（前置） |
| `10` org-playbook | 营销侧 + 销售侧（线索/折扣/ABM）落地 |
| `11` production-architecture | 数据工程、重训、服务、CPOG 式架构 |

**输出与交付**
| Ref | 主题 |
|-----|------|
| `12` html-report-output | 6 元素决策备忘 + 17 节分析，provenance 渲染 |
| `13` product-country-pipeline | 8 阶段产品×国家流水线 |
| `14` d-dimension-reviewer | D 维度生成门 + 独立对抗评审，open-blocking → BLOCKED 预算联动 |
| `15` writing-rules | 语言策略、可证伪义务、诚实状态词、反 slop、叙事与理论可用性原则 |
| `16` estimation-discipline | 四种 provenance 状态、Fermi 链、基准不对称、敏感度排序的 Missing 台账 |
| `17` category-portfolio-diagnostic | 整类目货盘诊断，位于单品 pipeline 上游：6 审视镜（2 市场 + 4 审 P）、严重度受证据等级封顶、SKU 裁决（加大投入/维持现状/收割利润/计划退市）、4P 矩阵；选出的「加大投入」SKU 下沉至 ref 13 → 04 |

</details>

---

## 🔧 脚本

每次 push 由 CI 自动复验（[`.github/workflows/validate.yml`](.github/workflows/validate.yml)）：流水线端到端跑全部 5 个核心脚本、用 provenance 合约校验每个示例 config、并把每个 config 渲染成 HTML。每个脚本都对应报告里的一个门控环节。

| Script | 用途 | 报告桥接 |
|--------|------|----------|
| `power_analysis.py` | uplift 功效：检测增量差异的样本量（≈ A/B 的 4×） | §9 门 + §13 时长 |
| `qini_auuc.py` | Qini 曲线、AUUC + bootstrap CI、分桶校准、双模型对比 | §11 AUUC 上线门 |
| `ope_estimators.py` | IPS / SNIPS / DR off-policy 评估 + support 检查 | §14 OPE support |
| `hte_starter.py` | T / X / DR-learner 起手式（sklearn，可换 EconML/CausalML） | — |
| `policy_budget.py` | λ* 预算约束分配（ref 06 背包/影子价格）、随机化保留集上的 IPW 政策价值、利润-预算曲线 | Layer 3 决策工具 |
| `generate_report.py` | 决策备忘 HTML 生成器（v2）和交互式看板渲染器。**强制 provenance 合约**；report 模式含 5 张因果逻辑交互图（ECharts）和三档深度 `--depth quick/standard/deep`；dashboard 模式输出单位经济、渠道筛选、热力图、treatment gates、evidence ledger 组成的 board-style cockpit | **HTML 输出入口** |

---

## 🧭 方法论立场

写进规则、强制执行的硬约束：

1. **实验优先是硬规则** — 没有随机化数据先建 GCG/geo，不拿观察性日志硬估 CATE。
2. **诚实空白胜过虚假完整** — 每个数字非 sourced 即 assumed / derived / missing，没有第五种状态；`generate_report.py` 构建时强制校验。
3. **估计器走窄默认路径** — 不做综述；验证只认 Qini/AUUC + 分桶校准。
4. **四象限是沟通工具** — 线上决策用连续 τ̂ − 成本 + 预算约束。
5. **成熟度分级 L1→L2→L3，防跳级** — 多数团队应长期停在 L2。
6. **AI 角色有红线** — 无实验支撑不得宣布动作有效；LLM 评估不替代 holdout。
7. **客户声音是 Hypothesis 级** — 评论/情绪只生成「要测什么」，永远不证明增量（ref 00b）。

---

## 📦 依赖与示例

```bash
pip install numpy pandas scipy scikit-learn matplotlib
```

生产建议换 [EconML](https://github.com/py-why/EconML) / [CausalML](https://github.com/uber/causalml)。

**示例配置**（`.claude/skills/sm-causal-personalization/examples/`）：

- `sample-sku-en-config.json` — 英文，标准单品报告（虚构品牌与产品）
- `sample-sku-zh-config.json` — 中文版，含完整 UI 标签覆盖、TL;DR 总结页和 ECharts 本地化（虚构品牌与产品）
- `aurora-airpurifier-category-config.json` — 类目货盘诊断（ref 17），虚构品牌/型号示例：`report_type=category_portfolio`

每个 config 的预渲染 HTML 放在 [`examples/rendered/`](.claude/skills/sm-causal-personalization/examples/rendered) — 不跑脚本即可预览交付物长什么样。

---

## 📄 许可

[Apache License 2.0](LICENSE) © 2026 alexwang91.
*依据 Apache-2.0 授权——可自由使用、修改和分发，需保留署名和专利授权声明。*
