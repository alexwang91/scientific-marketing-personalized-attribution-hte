<div align="center">

# Scientific Marketing · Causal Personalization

### 营销因果个性化决策系统 · HTE / Uplift / Incrementality — packaged as a Claude Code skill

[![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-6E56CF)](https://claude.ai/code)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](#-依赖--示例--dependencies--examples)
[![References](https://img.shields.io/badge/references-18-44883e)](#-参考库--reference-library)
[![Scripts](https://img.shields.io/badge/scripts-5%20(validated)-blue)](#-脚本--scripts)
[![Provenance contract](https://img.shields.io/badge/numbers-sourced%20%C2%B7%20assumed%20%C2%B7%20derived%20%C2%B7%20missing-orange)](#-方法论立场--methodology-stance)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

**传统个性化问「谁最可能买」。因果个性化问「我的动作让谁*多*买了」。**
*Traditional personalization asks who is likely to buy. Causal personalization asks who bought **more because of your action**.*

τ(x) = E[Y(1) − Y(0) | X = x]

[快速开始 / Quickstart](#-快速开始--quickstart) ·
[能力 / What it does](#-这是什么--what-it-does) ·
[工作原理 / How it works](#-工作原理--how-it-works) ·
[参考库 / References](#-参考库--reference-library) ·
[方法论 / Methodology](#-方法论立场--methodology-stance)

</div>

---

## ✨ 这是什么 / What it does

一个把营销因果推断**做成可执行决策流程**的知识库，打包为 Claude Code agent skill。
不是一个模型，而是一套 AI 辅助的因果决策系统：

- **AI 负责生成** — 动作变体、从非结构化数据（评论/客服/销售记录）提取上下文、写实验文档、解释模型、监控漂移。
- **因果方法负责判断** — 动作是否有*增量*价值（τ(x)），而不是相关性。
- **制度负责兜底** — 实验优先、provenance 合约、对抗式评审、合规红线。

A decision system, not a single model: the LLM generates and extracts; causal
methods judge incrementality; institutional rules (experiment-first, a number
provenance contract, adversarial review, compliance red lines) keep it honest.

---

## 🖼 证明 / Proof

脚本是跑通验证过的，不是伪代码。下图为 `scripts/qini_auuc.py` 的真实输出：

<div align="center">

![Qini / AUUC curve — example output of scripts/qini_auuc.py](qini_curve.png)

*Qini 曲线：横轴=按预测 uplift 排序的触达比例，纵轴=累计增量。模型曲线与随机线之间的面积 = 模型创造的价值。*

</div>

---

## 🚀 快速开始 / Quickstart

```bash
git clone https://github.com/alexwang91/scientific-marketing-personalized-attribution-hte.git
cd scientific-marketing-personalized-attribution-hte
```

Claude Code 会自动加载 `.claude/skills/` 下的 skill。问任何关于**营销增量、uplift、
实验设计、发券策略、线索路由、归因 vs 增量**的问题即触发——包括大白话版的
「这个客户该不该发优惠券」「我的广告到底有没有用」「谁该投、谁该跳过」。

生成一份决策报告 / generate a decision report:

```bash
cd .claude/skills/sm-causal-personalization/scripts
python generate_report.py --config ../examples/ax3-romania-config.json --output report.html
python generate_report.py --config ../examples/ax3-romania-config.json --validate-only   # 仅校验 provenance 合约
python generate_report.py --demo > demo.html                                              # 最小 schema 示例
```

跑核心脚本 / run the core scripts:

```bash
python power_analysis.py     # uplift 实验功效：检测增量差异所需样本（≈ 标准 A/B 的 4×）
python qini_auuc.py          # Qini / AUUC + bootstrap CI + 分桶校准
python ope_estimators.py     # IPS / SNIPS / Doubly-Robust off-policy 评估 + support 检查
python hte_starter.py        # T / X / DR-learner 起手式（sklearn，可换 EconML / CausalML）
```

---

## 🏗️ 工作原理 / How it works

**四层生产架构 / four-layer production architecture:**

```
Layer 1 · 数据与实验资产    RCT 日志 + 倾向性 P(t|x) + GCG + 历史实验（每个实验都是可复用的评估资产）
Layer 2 · 效应估计          τ̂(x) via DR-learner / Causal Forest / X-learner（既校准又排序；收入用 ZILN 损失）
Layer 3 · 决策与分配        策略 π(x)：argmax + λ* 预算约束 + OPE 上线门；大动作空间用 MIPS/OffCEM
Layer 4 · 生成与服务（可选）LLM embedding 作特征（不进决策回路）；文案个性化服务层
```

**成熟度三级，禁止跳级 / maturity ladder (do not skip):**

| Level | 内容 | 多数团队 |
|-------|------|---------|
| **L1** | GCG + 回溯式 uplift 分析 | 所有团队的起点 |
| **L2** | 离线策略学习 + OPE 验证 + 周期重训 | **应长期停在这里** |
| **L3** | 上下文 bandit 在线学习 | 仅当动作多、环境变化快时 |

**产品×国家流水线 / product × country pipeline**（ref 13）：Stage 0 本地市场情报 →
证据 → 单位经济 → 渠道筛（可在此终止）→ 维度 → 评审 → 测试 → 渲染报告。

---

## 📚 参考库 / Reference library

每个 reference 固定模板：**何时用 → 决策树 → 最小必要数学 → 分步操作 → 常见死法 → 验收清单 → 文献**。决策指南，不是教科书。

<details>
<summary><b>展开全部 18 篇 / expand all 18 references</b></summary>

**研究与立项 / research & framing**
| Ref | 主题 |
|-----|------|
| `00` local-market-intelligence | 动态市场扫描内核：7 轴定位 → 迁移假设台账 → 差异化假设 → 排序 → 再编排 |
| `00b` customer-voice-competitor-scan | 按互动量挖真人评论/竞品，填充 Push/Pull/Habit/Anxiety 四力与候选维度（voice = Hypothesis 级，只生成「要测什么」） |
| `01` problem-framing | 利润口径；attribution × incrementality × MMM 三角 |

**核心因果链 / core causal chain**
| Ref | 主题 |
|-----|------|
| `02` treatment-design | 动作库、treatment card、四力机制、LLM 变体爆炸的应对 |
| `03` experiments | 识别阶梯、GCG 制度、HTE 功效、倾向性日志 |
| `04` hte-estimation | learner 选型默认路径；Qini/AUUC 验证三件套 |
| `05` uplift-segmentation | 四象限（沟通用）、Ascarza 教训、sleeping dogs |
| `06` policy-nbt | 策略价值、预算约束 λ*、OPE 上线流程 |
| `07` bandits-online | L3 准入四问、Thompson Sampling、漂移与回路 |
| `08` long-term-value | surrogate index、pull-forward、长期 holdout |

**治理与落地 / governance & rollout**
| Ref | 主题 |
|-----|------|
| `09` governance | 特征四问、红队清单、anti-persona、AI 角色红线（前置） |
| `10` org-playbook | 营销侧 + 销售侧（线索/折扣/ABM）落地 |
| `11` production-architecture | 数据工程、重训、服务、CPOG 式架构 |

**输出与交付 / output & delivery**
| Ref | 主题 |
|-----|------|
| `12` html-report-output | 6 元素决策备忘 + 17 节分析、provenance 渲染 |
| `13` product-country-pipeline | 8 阶段产品×国家流水线 |
| `14` d-dimension-reviewer | D 维度生成门 + 独立对抗评审，open-blocking → BLOCKED 预算联动 |
| `15` writing-rules | 语言策略、可证伪义务、诚实状态词、反 slop、叙事与理论可用性原则 |
| `16` estimation-discipline | 四种 provenance 状态、Fermi 链、基准不对称、敏感度排序的 Missing 台账 |

</details>

---

## 🔧 脚本 / Scripts

全部跑通验证。每个脚本都对应报告里的一个门控环节。

| Script | 用途 | 报告桥接 |
|--------|------|----------|
| `power_analysis.py` | uplift 功效：检测增量差异的样本量（≈ A/B 的 4×） | §9 门 + §13 时长 |
| `qini_auuc.py` | Qini 曲线、AUUC + bootstrap CI、分桶校准、双模型对比 | §11 AUUC 上线门 |
| `ope_estimators.py` | IPS / SNIPS / DR off-policy 评估 + support 检查 | §14 OPE support |
| `hte_starter.py` | T / X / DR-learner 起手式（sklearn，可换 EconML/CausalML） | — |
| `generate_report.py` | 决策备忘 HTML 生成器（v2）。**强制 provenance 合约**：任何非 sourced/assumed/derived/missing 的数字一律构建失败；含 5 张承载因果逻辑的交互图（ECharts） | **HTML 输出入口** |

---

## 🧭 方法论立场 / Methodology stance

写进规则、强制执行的硬约束：

1. **实验优先是硬规则** — 没有随机化数据先建 GCG/geo，不拿观察性日志硬估 CATE。
2. **诚实空白胜过虚假完整** — 每个数字非 sourced 即 assumed / derived / missing，没有第五种状态；`generate_report.py` 构建时强制校验。
3. **估计器走窄默认路径** — 不做综述；验证只认 Qini/AUUC + 分桶校准。
4. **四象限是沟通工具** — 线上决策用连续 τ̂ − 成本 + 预算约束。
5. **成熟度分级 L1→L2→L3，防跳级** — 多数团队应长期停在 L2。
6. **AI 角色有红线** — 无实验支撑不得宣布动作有效；LLM 评估（含多智能体模拟）不替代 holdout。
7. **客户声音是 Hypothesis 级** — 评论/情绪只生成「要测什么」，永远不证明增量（ref 00b）。

---

## 📦 依赖 / 示例 / Dependencies & Examples

```bash
pip install numpy pandas scipy scikit-learn matplotlib
```
生产建议换 [EconML](https://github.com/py-why/EconML) / [CausalML](https://github.com/uber/causalml)。

**示例配置 / example configs**（`.claude/skills/sm-causal-personalization/examples/`）：

- `ax3-romania-config.json` — 英文，标准报告
- `fit5pro-hungary-config.json` / `fit5pro-hungary-zh-config.json` — 匈牙利市场，英 / 中双版本（中文版含本地化图表与 TL;DR 总结页）

---

## 📄 License

[Apache License 2.0](LICENSE) © 2026 alexwang91.
*Licensed under Apache-2.0 — free to use, modify, and distribute with attribution and the included patent grant.*
