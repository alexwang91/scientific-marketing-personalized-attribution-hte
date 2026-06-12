# 08 · 长期价值与 Surrogate

## 什么时候用

被问"短期有效长期呢"的时候；定 reward/优化目标的时候；
补贴策略要算 LTV 账的时候；实验窗口定多长的时候。

## 为什么短期窗口会系统性骗人

- **Sleeping dog 的伤害在长期**：退订、品牌疲劳、免打扰名单增长，14 天窗口看不见
- **补贴透支 LTV**：发券拉来的转化里，一部分是把未来的原价购买提前成今天的折价购买（pull-forward），还训练用户等券（价格锚点被改写）
- **渠道挤占**：付费拉来的"新客"部分是自然流量的换皮（见 01 增量口径）

短期窗口测出的 τ 对这三类效应全部为盲。

## Surrogate Index（短期代理长期的正规方法）

直接等 12 个月观察 LTV，实验迭代速度死掉。Athey-Chetty-Imbens 的
surrogate index 方法：

```
1. 用一份历史长期数据，建模 长期Y ~ f(短期指标向量 S)
   S = (7/14/30天复购, 客单, 活跃频次, 退订, 投诉, 品类宽度, …)
2. 实验只跑短期，测 treatment 对 S 的效应
3. 长期效应估计 = f(S) 的 treatment 效应
```

**成立条件（必须定期复核）**：treatment 影响长期 Y 只通过 S
（surrogacy 假设）。某些动作会绕过 S 直接伤长期（如品牌伤害），
所以需要下面的长期 holdout 兜底。

**实用要点**：S 要用**指标向量**而不是单一指标——单一短期指标
（如首购转化）最容易被策略 game；向量里务必包含负向指标（退订、投诉）。

## 长期 holdout（制度兜底）

- 从 GCG 中保留一个**永久子集**（如 1%），长年不触达 → 测 CRM 体系的累积效应
- 每个重大策略保留一个**长期对照组**跑 6–12 个月 → 验证 surrogate 估计有没有系统性偏差
- 年度复盘：surrogate 预测的长期效应 vs 长期对照实测，偏差大就重建 f(S)

## 增量 LTV 口径

```
增量LTV(x,t) = Σ_未来窗口 [E[利润|treated] − E[利润|control]] 折现
             − 补贴成本 − 提前消费的侵蚀（pull-forward 修正）
```

Pull-forward 检测：treated 组短期转化高、随后一段时间转化**低于** control
（曲线交叉）就是把未来需求搬到了现在。把观察窗拉长到交叉点之后再算净效应。

## 操作步骤

1. 用历史数据建 surrogate index f(S)，记录训练时点和假设
2. 实验/bandit 的 reward 用 f(S) 而非裸转化（07）
3. 建永久 holdout 和策略级长期对照
4. 季度：检查 pull-forward 曲线交叉；年度：surrogate 偏差复核

## 常见死法

- **单一 surrogate 被 game**：优化"首购转化"，策略学会发大券，LTV 一年后现形
- **Surrogate 一次建好用三年**：人群和产品变了，f(S) 过期没人发现
- **实验 2 周下结论**：pull-forward 的交叉点在第 4–8 周，正效应是借来的
- **长期 holdout 被运营借走**："双十一冲量先把那 1% 放出来用" → 永久基线没了

## 验收清单

- [ ] Reward/目标里有 surrogate index，不是裸短期转化
- [ ] S 是含负向指标的向量
- [ ] 永久 holdout + 策略级长期对照在跑
- [ ] Pull-forward 检查季度化，surrogate 复核年度化

## 文献指针

- Athey, Chetty, Imbens & Kang (2019) "The Surrogate Index" — 方法本体
- Yang, Eckles et al. — 工业界 surrogate 应用（Netflix/Meta 系公开材料）
- Gupta et al. (2006) "Modeling Customer Lifetime Value" — LTV 口径
- Anderson & Simester 系列 — 促销的长期效应实证（深折扣训练等券行为）
