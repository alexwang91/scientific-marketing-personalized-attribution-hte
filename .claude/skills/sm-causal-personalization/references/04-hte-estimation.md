# 04 · HTE 估计与模型验证

## 什么时候用

有了随机化数据要估 τ(x) 的时候；选估计器的时候；
被问"这个 uplift 模型靠不靠谱"的时候。

## 目标量

```
τ(x) = E[Y(1) − Y(0) | X = x]    （CATE：条件平均处理效应）
```

不是预测谁会买（propensity），是预测"营销有没有改变他"。
**根本困难：同一个人永远只能观察到一个潜在结果**，所以 uplift 模型
不能像普通 ML 那样拿 label 算 AUC——验证方法完全不同（见下）。

## 默认估计路径（窄路径，不做综述）

```
数据是随机化的吗？ ─ 否 → 回 03，别在这里硬估
│
├─ 二元 treatment，样本充足（每组 ≥ 数万）
│   → 默认：Causal Forest（EconML CausalForestDML）或 DR-learner
│     理由：DR-learner 对 nuisance 模型误差二阶鲁棒；causal forest 自带置信区间
│
├─ treatment / control 样本悬殊（如 95/5 的 GCG 数据）
│   → X-learner（专为不平衡设计，小组借大组的信息）
│
├─ 多个 treatment（动作库）
│   → 每个 treatment 对 control 分别估 τ_t(x)，共享 outcome 基线模型 μ₀(x)
│     动作多到不可分估 → treatment 特征化（见 02）
│
└─ 连续/剂量型 treatment（折扣深度）
    → Double ML（DML）剂量响应
```

各 learner 一句话定义：
- **T-learner**：treated 和 control 各训一个 μ₁(x)、μ₀(x)，τ̂ = μ̂₁ − μ̂₀。简单，不平衡时差。
- **S-learner**：一个模型把 T 当特征。treatment 效应弱时会被正则化抹掉，慎用。
- **X-learner**：T-learner 基础上交叉插补伪效应再回归，用倾向性加权合成。不平衡首选。
- **DR-learner**：构造 doubly robust 伪结果再回归。nuisance 有一个估对就一致。
- **Causal Forest**：广义随机森林按效应异质性分裂，honest splitting 给有效置信区间。

库选择：**EconML**（微软，DML/DR/森林全）、**CausalML**（Uber，uplift 树和业界口径）。
起手代码见 `scripts/hte_starter.py`（sklearn 纯实现，可平移到上述库）。

## 验证：uplift 模型唯一合法的三件套

**禁止用 AUC/accuracy 验证 uplift 模型**——你没有个体级的 τ label。

1. **Qini 曲线 / AUUC**：按 τ̂ 从高到低排序，逐步扩大投放比例，画累积增量曲线。
   曲线越凸、AUUC 越大，排序能力越强。对比基线：随机排序（对角线）和
   propensity 排序（常见反面教材）。
2. **分桶增量校准**：按 τ̂ 分十桶，每桶内算实际的 treated − control 差，
   对照桶内平均 τ̂。好模型应该单调且校准（预测 3% 的桶实际也接近 3%）。
3. **持出集策略价值**：用验证集模拟"只投 τ̂ 前 k% 的人"的增量利润，
   和现行策略比（完整版是 06 的 OPE）。

三件套实现见 `scripts/qini_auuc.py`。

## 置信区间与多重检验

- Causal forest 的 honest CI 可直接用于"这个子群效应是否显著非零"
- **事后翻子群必须校正**：50 个子群挑显著 ≈ 纯噪声。预注册子群清单（03），
  或用 Benjamini-Hochberg 控 FDR
- **Winner's curse**：选出来的"最优子群"效应必然高估，上线前缩水预期
  （shrinkage / 用另一份持出集重估）

## 操作步骤

1. 确认数据来源是随机化的，拿到倾向性（GCG 比例或实验分流比）
2. 特征 X 全部用 **treatment 决策时刻之前** 的值（防泄漏，见下）
3. 按默认路径选 learner，训练时用 cross-fitting（防过拟合污染 nuisance）
4. 跑验证三件套，AUUC 显著优于随机 + 分桶校准单调，才算可用
5. 输出：τ̂(x) 分数 + 置信区间 + 验证报告，交给 05/06

## 常见死法

- **特征泄漏**：用了 treatment 之后的行为特征（如"是否点开了那条消息"）——τ̂ 完美但全错
- **用 propensity 思维验证**："模型 AUC 0.85 很好"——AUC 测的是预测谁买，不是预测谁被改变
- **样本不够硬分**：每组几千样本训 causal forest，Qini 曲线在持出集上变直线
- **拿观察性数据当随机数据**：忘了这批日志是老定向策略产生的，τ̂ 学到的是定向规则
- **不做校准只看排序**：排序对但量级错 2 倍，06 的利润优化全错

## 验收清单

- [ ] 数据随机化来源确认，倾向性已知
- [ ] 特征截止时间 < treatment 决策时间
- [ ] Learner 按默认路径选择，理由成文
- [ ] Qini/AUUC 显著优于随机基线（持出集）
- [ ] 分桶校准单调且量级可信
- [ ] 子群结论过了多重检验校正

## 文献指针

- Künzel et al. (2019, PNAS) "Metalearners for estimating heterogeneous treatment effects" — S/T/X-learner
- Kennedy (2023) "Towards optimal doubly robust estimation of heterogeneous causal effects" — DR-learner
- Wager & Athey (2018, JASA) "Estimation and Inference of Heterogeneous Treatment Effects using Random Forests" — causal forest
- Chernozhukov et al. (2018) "Double/Debiased Machine Learning" — DML
- Gutierrez & Gérardy (2017) "Causal Inference and Uplift Modelling: A Review" — uplift 评估口径
- 工具：EconML (Microsoft)、CausalML (Uber)
