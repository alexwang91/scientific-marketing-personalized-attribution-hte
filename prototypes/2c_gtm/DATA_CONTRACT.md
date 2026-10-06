# 统一经营输入合同 v1.0

机器合同：[schemas/input.schema.json](schemas/input.schema.json)。样例：[data/demo.json](data/demo.json)。`validate_input()` 同时检查 schema、跨行库存连续性、数量约束与实验时间。

**粒度**：国家 ISO2 × SKU × 销售渠道（online / retail）× 周起始 ISO 日期。媒体渠道属于行动属性，与销售渠道分开。每条记录代表完整、已结束的经营周。规划在最后完整周结束后进行，输入 closing stock 为下一周 opening stock；所有到货日数从下一周开始计算。国家与 SKU 必须使用唯一 ID，禁止合并国家数据。

| 字段 | 口径 / 用途 |
|---|---|
| country / sku / channel / period | 唯一联合主键，period 为周一；同一序列连续每七天一条 |
| category / scenario / listed | 品类、sport/commute/gift 默认场景、是否已上市 |
| price_eur / cost_eur | 每台净售价和落地成本，EUR，不含 VAT |
| channel_fee_pct / return_handling_eur | 按扣退款后的收入计提渠道费；每台退货处理成本 |
| opening_stock_units / sell_in_units / closing_stock_units | 可售期初库存、本周收货、可售期末库存 |
| sell_out_units / returns_units | 本周售给消费者的毛销量、归属于本周销量且已退款的退货数 |
| inbound_units / inbound_due_days / lead_time_days | 下一批确定到货量、从规划周开始算的到货时间、常规补货交期 |
| discount_pct | 待测试阶段优惠；只用于独立 Price 毛利可行性检查 |
| content_readiness / traffic_index | [0,1] 假设评分；内容低于 0.6 暂停媒体投放，traffic 暂供经营诊断展示，不估计其因果效应 |
| marketing_spend_eur | 已结束周实际演示投入；不用于因果估计 |
| seasonality_index | 显式季节倍率；历史基线先除历史倍率，再乘当前倍率，v1 数据设为 1 |
| provenance | 固定 fictional_fixture，禁止混入真实数据 |

根字段：`fictional=true`、`contract_version=1.0`、`period_days=7`、`planning_budget_eur`、`rows`、`population_cells`、`experiments`。

`population_cells[country]` 包含三个场景、虚构人口权重与 digital/intent/price/premium 假设特征。确定性最大余数法生成 120 人，样本权重总和与原 cells 一致。这些数据没有真实人口校准。

`experiments[]` 包含 row_id、scenario、media_channel、处理/对照人数及转化、available_on；source 固定 simulated_randomized_fixture。实验匹配必须同时满足国家、SKU、销售渠道、历史快照周、场景、媒体动作。示例 available_on 早于快照周开始，验证器拒绝未来实验泄漏。实际扩展应建立独立 experiment_id、assignment、曝光、cohort、完成及可用时间。

## 经营公式

- 可售期末 = 期初 + sell in − 毛 sell out。返回商品进入隔离区，不增加可售库存。
- 退货率 = returns / gross sell out；没有销量则为零，不能据此证明体验好。
- 贡献/台 = price × (1 − 退货率) × (1 − 渠道费率) − cost − 退货率 × 退货处理费。
- 日需求 = 历史季节调整后的周均毛 sell out / 7。
- 库存天数 = 期末可售库存 / 日需求；无需求基线时保持空值。
- 下一周总余量 = 期末库存 + 7 天内到货 − 基础周需求。
- 到货前余量 = 期末库存 − 日需求 × min(到货日数,7)。投放增量上限取上述两种余量的较小值，下限为零。该保守规则假定增量需求可能早于到货。
- 缺货风险：库存天数 < 常规交期；积压风险：>56 天。缺货风险不总是完全冻结投放：存在到货前增量余量时允许受限测试。
- 硬阻塞：高退货 >10%、未上市、单位贡献 ≤0、无增量余量、内容 <0.6 或模拟效应下界 ≤0。

## 输出

`plan.decisions[]` 以完整联合 ID 保留输入、基线、库存余量、贡献毛利、风险、场景、媒体分数、证据 signal、九部分 activation plan、4P、预算、增量、净利润和下一步负责人/日期。

`allocation`、`frontier` 为复用引擎的汇总。引擎以完整联合 ID 作为内部 sku key，避免把同 SKU 不同国家/渠道混在一起。`as_of` 为完整周末，`decision_period` 为下一周起始日。

`data/outcomes.json` 为独立模拟未来经营结果，完全不参与选品、响应估计或预算。`verification` 同时展示计划与模拟后测，但明确禁止无对照归因。
