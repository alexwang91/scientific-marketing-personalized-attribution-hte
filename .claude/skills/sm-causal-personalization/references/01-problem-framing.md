# 01 · 问题定义与测量框架

## 什么时候用

项目启动时；被问"做这个营销有没有用、怎么定指标"；团队把 attribution
报表当因果结论用的时候；定 KPI 和护栏指标的时候。

## 决策树：先确认要回答的是哪一层的问题

```
你要回答什么？
├─ 预算在渠道/大盘之间怎么分 → MMM（边际 ROI，季度级）
├─ 这次转化算哪个触点的功劳 → Attribution / MTA（分钱规则，相关性）
├─ 这个 campaign 整体有没有增量 → Incrementality test（geo / holdout，ATE）
└─ 对这个人做这个动作值不值 → HTE / uplift（τ(x)，本 skill 主线）
```

**三角验证（triangulation）**：现代营销测量的标准架构是 MMM × 增量实验 ×
attribution 三者互相校准——用增量实验校准 MMM 的系数，用 MMM 管预算层，
attribution 只做运营层的快速反馈，不做预算依据。HTE 是把 incrementality
做到个人粒度，是 attribution 想逼近而逼近不了的东西。

**为什么 attribution 不是因果**：MTA 分钱给"出现在转化路径上的触点"，
但 sure things 的路径上也全是触点——他们本来就会买。last-click 高估
品牌词搜索、低估上层漏斗，是被增量实验反复证实的系统性偏差。
Cookieless 时代三方触点数据继续退化，一方实验的地位只会更高。

## 定义清单（每个项目必须先写完才动手）

1. **Y（outcome）**：转化 / 复购 / 客单 / 留存 / 退订，明确观察窗口（如触达后 14 天）
2. **业务目标量**：增量利润，不是转化率：

   ```
   增量利润(x,t) = τ_revenue(x,t) × 毛利率
                 − 券面额 × P(核销|treated) ← 核销成本只在 treated 发生
                 − 渠道成本（短信/广告按次计费）
                 − E[长期负效应]（退订、疲劳、品牌，见 08）
   ```

3. **护栏指标（guardrails）**：退订率、投诉率、触达频率上限、毛利下限、
   退货率。任何 policy 上线都带护栏，破线自动回滚。
4. **时间窗**：短期代理窗口（决策用）+ 长期验证窗口（季度复盘用，见 08）
5. **决策单元**：用户 / 账户（toB，见 10）/ 门店 / 地域

## 操作步骤

1. 用上面的决策树确认问题层级，写一句话问题陈述：
   "对【人群】做【动作】，在【窗口】内能否带来【增量利润 ≥ X】，护栏为【…】"
2. 写利润等式，让财务/分析确认口径（毛利率、核销率、成本归集）
3. 定护栏和回滚条件
4. 确认六大依赖（见 SKILL.md），缺实验数据先走 03
5. 治理预审（09）——在写任何代码之前

## 常见死法

- **拿 attribution 当因果**："搜索品牌词 ROI 最高所以加预算" → 增量实验一测全是 sure things
- **只看转化不看增量利润**：发券给本来就会买的人，转化率好看，毛利烧光
- **没有护栏指标**：转化涨了，退订也涨了，半年后名单废了
- **窗口太短**：14 天看到正效应，90 天看 LTV 被透支（见 08）
- **问题层级错配**：用 HTE 模型回答预算分配问题（该用 MMM），或用 MMM 回答个性化问题

## 验收清单

- [ ] 一句话问题陈述写出来了，且属于 HTE 层（否则转 MMM/实验）
- [ ] 利润等式有财务确认的口径
- [ ] Y、窗口、决策单元、护栏全部成文
- [ ] 六大依赖逐条核过，缺项有补齐计划
- [ ] 治理预审通过（09）

## 文献指针

- Kohavi, Tang & Xu, *Trustworthy Online Controlled Experiments* (2020) — 实验文化与陷阱大全
- Blake, Nosko & Tadelis (2015) "Consumer Heterogeneity and Paid Search Effectiveness: eBay" — 品牌词广告零增量的经典实证
- Lewis & Rao (2015) "The Unfavorable Economics of Measuring the Returns to Advertising" — 为什么广告增量天然难测
- Gordon et al. (2019, Marketing Science) — Facebook 实验 vs 观察性方法的大规模对比，观察性方法系统性失准
