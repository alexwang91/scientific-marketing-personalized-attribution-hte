# Scientific Marketing · 因果个性化 / Personalized Attribution / HTE

营销与销售场景下的因果个性化（causal personalization）方法论知识库，
打包为 Claude Code agent skill。

**核心问题**：传统个性化问"谁最可能买"，因果个性化问"我的动作让谁多买了"
（τ(x) = E[Y(1)−Y(0)|X=x]）。这是一个 AI-assisted causal decisioning system：
AI 生成动作、提取上下文，因果方法判增量，实验制度兜底。

## 结构

```
.claude/skills/sm-causal-personalization/
├── SKILL.md                  # 路由：心智模型、成熟度三级（L1/L2/L3）、决策树
├── references/
│   ├── 01-problem-framing.md       # 利润口径；attribution × incrementality × MMM 三角
│   ├── 02-treatment-design.md      # 动作库、treatment card、LLM 变体爆炸的应对
│   ├── 03-experiments.md           # 识别阶梯、GCG 制度、HTE 功效、倾向性日志
│   ├── 04-hte-estimation.md        # learner 选型默认路径；Qini/AUUC 验证三件套
│   ├── 05-uplift-segmentation.md   # 四象限（沟通用）、Ascarza 教训、sleeping dogs
│   ├── 06-policy-nbt.md            # 策略价值、预算约束 λ*、OPE 上线流程
│   ├── 07-bandits-online.md        # L3 准入四问、Thompson Sampling、漂移与回路
│   ├── 08-long-term-value.md       # surrogate index、pull-forward、长期 holdout
│   ├── 09-governance.md            # 特征四问、红队清单、AI 角色红线（前置）
│   └── 10-org-playbook.md          # 营销侧 + 销售侧（线索/折扣/ABM）落地
└── scripts/                  # 全部跑通验证
    ├── power_analysis.py     # uplift 功效计算（HTE ≈ 4× A/B 样本）
    ├── qini_auuc.py          # Qini / AUUC / 分桶校准
    ├── hte_starter.py        # T / X / DR-learner 起手式（sklearn）
    └── ope_estimators.py     # IPS / SNIPS / DR + support 检查
```

## 使用

克隆本仓库后，Claude Code 自动加载 `.claude/skills/` 下的 skill。
问任何营销增量、uplift、实验设计、发券策略、线索路由相关问题即触发。

脚本依赖：`pip install numpy pandas scipy scikit-learn matplotlib`
（生产建议换 [EconML](https://github.com/py-why/EconML) /
[CausalML](https://github.com/uber/causalml)）。

## 方法论立场（写进规则的六条）

1. 实验优先是硬规则：没有随机化数据先建 GCG/geo，不拿观察性数据硬估 CATE
2. 估计器走窄默认路径，不做综述；验证只认 Qini/AUUC + 分桶校准
3. 四象限是沟通工具，线上决策用连续 τ̂ − 成本 + 预算约束
4. 成熟度分级 L1→L2→L3，防跳级；多数团队应长期停在 L2
5. AI 角色有红线：不得在无实验支撑时宣布动作有效，LLM 评估不替代 holdout
6. 每个 reference 固定模板：决策树 → 公式 → 步骤 → 常见死法 → 验收清单 → 文献
