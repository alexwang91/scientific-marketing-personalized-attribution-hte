---
name: sm-causal-personalization
description: >
  因果个性化 / Causal Personalization 决策系统方法论。Use when 讨论营销增量、
  uplift modeling、HTE、CATE、incrementality、发券策略、营销实验设计、holdout、
  全局对照组 GCG、geo-lift、next best action/treatment、策略学习 policy learning、
  off-policy evaluation、contextual bandit、attribution 与增量的关系、线索路由、
  折扣审批、ABM 实验，或用户提到"科学营销"、"增量测量"、"因果推断在营销中的应用"。
  覆盖从问题定义、实验设计、HTE 估计、人群分层、策略优化到治理合规的完整链路。
---

# Scientific Marketing: 因果个性化决策系统

## 核心心智模型

**传统个性化问"谁最可能买"，因果个性化问"我的动作让谁多买了"。**

这不是一个模型模块，而是一个 AI-assisted causal decisioning system：

- **AI 负责**：生成 treatment 变体、从非结构化数据提取 context、写实验文档、解释模型、监控漂移
- **因果方法负责**：判断动作有没有增量价值（τ(x) = E[Y(1)−Y(0)|X=x]）
- **红线**：AI 不得在没有实验或识别策略支撑时宣布"这个动作有效"。LLM 评估不能替代 holdout。

三个概念的关系（详见 01）：

| 问题 | 工具 | 层级 |
|------|------|------|
| 预算在渠道间怎么分 | MMM | 渠道/预算层 |
| 这次转化算谁的功劳 | Attribution (MTA) | 触点层，相关性 |
| 对这个人做这个动作多带来多少 | HTE / uplift | 个人层，因果 |

HTE 就是"个人级 incrementality"，是 attribution 想逼近而逼近不了的东西。

## 测量成熟度三级（防止跳级）

- **L1**：全局对照组（GCG）+ 事后 uplift 分析。所有团队的起点。
- **L2**：离线 policy 学习 + OPE 验证 + 定期重训。多数团队应该在这里停很久。
- **L3**：contextual bandit 在线学习。只有动作多、环境变化快才需要。

**硬规则：没有随机化数据，第一步永远是建实验基础设施（GCG / geo），
而不是拿观察性数据硬估 CATE。** 营销日志的混杂极强——谁被触达本身就是
老定向策略决定的。观察性方法只作降级方案，且必须写出识别假设（见 03）。

## 决策树：用户的问题属于哪类

```
用户在问什么？
├─ "做这个营销/项目有没有用、怎么定指标" → 01-problem-framing
├─ "动作/创意/券怎么设计、AI 生成的变体太多怎么测" → 02-treatment-design
├─ "怎么设计实验、没有实验数据怎么办、样本要多少" → 03-experiments
├─ "怎么估计谁被影响了、用什么模型、模型怎么验证" → 04-hte-estimation
├─ "人群怎么分层、该投谁不该投谁" → 05-uplift-segmentation
├─ "给每个人选哪个动作、预算不够怎么分、新策略上线前怎么评估" → 06-policy-nbt
├─ "要不要上 bandit、在线学习怎么做" → 07-bandits-online
├─ "短期有效长期呢、LTV、surrogate" → 08-long-term-value
├─ "合规、公平、隐私、特征能不能用" → 09-governance（任何项目启动时都先过一遍）
└─ "组织怎么落地、营销/销售团队怎么配合、KPI 怎么定" → 10-org-playbook
```

## 实操脚本（scripts/）

| 脚本 | 用途 |
|------|------|
| `power_analysis.py` | uplift 实验功效计算：检测增量差异所需样本量（约为普通 A/B 的 4 倍） |
| `qini_auuc.py` | Qini 曲线、AUUC、分桶增量校准——uplift 模型唯一合法的验证方式 |
| `hte_starter.py` | T/X/DR-learner 起手式模板（sklearn 实现，可换 EconML/CausalML） |
| `ope_estimators.py` | IPS / SNIPS / Doubly Robust 离线策略评估 + support 检查 |

## 六大依赖（项目启动前自查）

1. **实验数据**：没有 RCT/holdout/geo/可信准实验，说不了"是营销导致的"
2. **动作定义**："发营销消息"太粗，"7折券+情绪话术+微信+48h窗口"才可学习
3. **利润口径**：增量利润 = 增量收入 − 补贴成本×核销率 − 渠道成本 − 长期负效应
4. **样本量**：CATE 很吃数据，分太细全是噪声（跑 power_analysis.py 确认）
5. **数据工程**：用户 ID、曝光/动作/结果日志、时间戳、成本、实验组标记、**倾向性日志 P(action|x)**
6. **组织执行**：营销团队要接受"不投某些高转化用户"（话术见 10）

## Reference 统一结构

每个 reference 按固定模板写：什么时候用 → 决策树 → 最少必要公式 →
操作步骤 → 常见死法 → 验收清单 → 文献指针。是决策指南不是教科书。
