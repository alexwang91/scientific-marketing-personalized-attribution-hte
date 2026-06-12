# 07 · 在线学习与 Contextual Bandit

## 什么时候用

被问"要不要上 bandit"的时候；动作多、创意频繁更新、离线重训跟不上的时候。

## 先确认你需要 L3（多数团队不需要）

```
□ 动作/创意数量大且持续上新（每周都有新臂）？
□ 环境非平稳（季节、库存、竞对动作快）？
□ 反馈快（数小时到数天内能观察到 Y）？
□ L2 已经跑顺（OPE、倾向性日志、护栏、双对照都有）？
```

四项没有全勾，留在 L2：离线 policy + 定期重训 + 固定探索流量，
便宜、可审计、够用。**动作少、环境稳的场景上 bandit 纯属自找麻烦**——
复杂度全要，收益没有。

## Contextual bandit 是什么

每次决策：看到 context x → 选动作 t → 观察 reward r。目标是累积 reward
最大化，同时持续探索。两个主流算法一句话：

- **Thompson Sampling**：对每个动作的效果保持后验分布，按后验采样选动作。实现简单、实践好用，默认选它。
- **LinUCB**：效果建模为 context 的线性函数，选"估计值 + 不确定性加成"最大的动作。

**探索的本质价值 = 持续的测量带宽**：探索流量就是自动化的持续实验，
让新臂能被评估、让漂移能被发现。bandit 天然记录倾向性（选择概率），
日志直接可用于 OPE——这是它和"硬编码规则"的根本区别。

## Reward 设计（bandit 防短视的真正机制）

"因果框架防止只追短期转化"不是一句口号，机制是三件事：

1. **Reward = 增量利润代理，不是点击/转化**：用 01 的利润等式，
   至少把券成本扣掉，否则 bandit 必然学会"给所有人发最大的券"
2. **Surrogate 校准**：短期 reward 必须用 08 的 surrogate index 对齐长期 LTV，
   季度复核短期-长期相关性是否仍成立
3. **常驻 GCG 不能撤**：bandit 内部臂间对比 ≠ 增量证据——所有臂都在
   "做营销"，bandit 只回答"做哪个好"，不回答"做了比不做好多少"。
   增量结论永远来自 bandit 流量 vs GCG。

## 漂移与反馈回路

- **漂移监控**：context 分布漂移（PSI 等）、各臂效果漂移（滚动窗口 vs 历史）、
  探索流量占比是否被压到失效
- **反馈回路**：策略改变人群——长期被发券的用户学会等券（价格锚点被
  策略本身改写）。检测手段：GCG 用户的基线行为 vs treated 人群的
  基线漂移；这也是固定 GCG 的价值（03）
- **新臂冷启动**：用 02 的 treatment 特征化让新臂继承相似臂的先验，
  而不是从均匀先验开始烧流量

## 操作步骤

1. 过"需要 L3"四项检查，没全勾就回 06
2. Reward 函数按利润等式写，财务确认口径
3. 默认 Thompson Sampling + treatment 特征（线性或浅树后验）
4. 流量结构：GCG（1–5%）+ bandit（其余），bandit 内部自带探索
5. 倾向性日志自动落库（bandit 天然有，确认接入数据仓库）
6. 漂移监控 + 护栏自动回滚 + 季度 surrogate 复核

## 常见死法

- **拿 bandit 内部对比当增量**："A 臂比 B 臂好 20%" ≠ "A 臂有增量"，可能两个都是负增量，GCG 才能揭穿
- **Reward 定义成点击**：bandit 一周内学会标题党/最大折扣
- **探索被运营关掉**："探索流量在浪费钱" → 三个月后所有估计过期，bandit 退化成定死规则
- **跳级上 L3**：倾向性日志、护栏都没有就上 bandit，出问题无法审计也无法回滚
- **非平稳不处理**：用全历史数据更新后验，季节切换后模型固执于过期结论（用滑动窗口或折扣因子）

## 验收清单

- [ ] "需要 L3"四项全勾
- [ ] Reward = 利润代理且过了 surrogate 校准
- [ ] GCG 在 bandit 之外常驻
- [ ] 倾向性日志入仓，OPE 可复用
- [ ] 漂移监控、最低探索比例、护栏回滚就位

## 文献指针

- Li et al. (2010) "A Contextual-Bandit Approach to Personalized News Article Recommendation" — LinUCB 经典
- Russo et al. (2018) "A Tutorial on Thompson Sampling"
- Amazon Science: causal contextual bandits 系列 — 因果约束下的 bandit
- Agarwal et al. (2016) "Making Contextual Decisions with Low Technical Debt" — 工业部署（Decision Service）
