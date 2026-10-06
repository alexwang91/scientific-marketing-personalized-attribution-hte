# 2C GTM：国家上市与营销经营比赛原型

国家团队先看 `country × SKU × channel × period` 的动销和库存，再选择运动、通勤或送礼场景，确定 4P 动作，分配营销预算，并在下一周期复查动销、库存、贡献毛利和退货。原型复用三个现有仓库的组件，新增经营输入与约束层。所有产品、价格、人群、交易及实验数据均为虚构。

## 运行

Python **3.10+**，运行原型无需 pip 安装、API key、网络或 LLM。

从 scientific-marketing 仓库根目录运行：

```bash
python prototypes/2c_gtm/server.py
# 浏览器打开 http://127.0.0.1:8765
```

完整 dashboard 支持国家、SKU、销售渠道筛选、预算修改、运动/通勤/送礼场景切换、4P 建议、证据详情、利润预算前沿、模拟后测与决策 JSON 下载。筛选后，所填写预算仅用于当前筛选范围，不代表已预留全区域预算。

离线快照与可复现输出：

```bash
python prototypes/2c_gtm/server.py --export prototypes/2c_gtm/demo-output
# 打开 demo-output/dashboard.html，可点击行查看详情和下载 JSON。
# 离线快照不支持改变筛选、人群或预算；重算请运行服务器。
python -m unittest discover -s prototypes/2c_gtm -p 'test_gtm.py' -v
node prototypes/2c_gtm/test_dashboard.cjs
```

Node 18+ 仅用于可选 JavaScript + HTTP 联调，不属于运行依赖。该测试使用 DOM 仿真，不覆盖真实浏览器渲染。此交付环境没有 Chromium 运行文件，因此没有声称完成浏览器视觉测试。

`data/demo.json` 为 3 国家 × 3 SKU × 2 渠道 × 3 周，共 54 条经营记录；`data/outcomes.json` 为独立模拟后测。`make_demo.py` 可重新生成两份输入；生成器不读取任何客户资料。

## 演示顺序

1. 打开默认页面：18 个当前经营单元，共 €5,000 可用预算。
2. 查看 HU / NOVA-W1 / online：选择运动，查看匹配此单元的模拟随机实验、库存约束和渠道计划。
3. 改成送礼：系统不迁移运动场景的实验结论，降至假设级，将此单元投放上限降至 €300。
4. 查看 GR / NOVA-W1 / online：到货前库存不能覆盖基础需求，投放为 €0，先补货。
5. 查看 RO / NOVA-T1：退货超过 10%，投放为 €0；建议先检查体验及服务。
6. 查看 RO / NOVA-B1 / retail：积压但内容尚未就绪，先完善陈列与本地内容，不能因为积压直接买流量。
7. 查看预算前沿与后测：区分计划、模拟结果和无法归因的差异；导出完整决策 JSON。

默认结果：建议投入 **€3,700**，保留 **€1,300**，阻塞 **10** 个单元。HU / NOVA-W1 / online 建议 €850，预测增量约 42.27 台，低于到货前可售余量 51.71 台。数字用于检验计算，不代表市场预测或比赛实际收益。

## 复用与新增

| 能力 | 复用来源 | 原型如何使用 |
|---|---|---|
| 加权合成人群 | Synthetic-population：`sample_persona_skeletons.py` | 每国生成 120 个确定性样本，保留权重与来源 cell |
| Media planner | Synthetic-population：`generate_channel_plan.py` / `run_channel_simulation.py` | 复用渠道池与 `simulate_one()`，传入本国、本场景实际样本 |
| 受众激活 | 本仓库 `generate_activation_plan.py` | 复用渠道代理人群、地域语言、落地页与排除规则 |
| 因果证据合同 | audience-activation-spec 两个 JSON schemas | 校验 research signal 与九部分 activation plan，禁止合成人群声明因果 HTE |
| 利润预算前沿 | 本仓库 `investment_schema.py` / `investment_engine.py` | 校验、筛选、边际回报排序与 €50 步长分配 |
| 经营输入和约束 | 新增 | 周度合同、库存对账、到货前约束、退货、贡献毛利、4P、独立后测 |

重要接线修正：上游 `build_simulation(plan, personas=...)` 在固定版本中忽略 personas 并使用默认 panel。此原型不调用该包装器，直接复用 `simulate_one()`，传入本国实际采样结果；上游文件保持原样。原型也移除了上游规划区间的统计置信区间标签。

详见 [输入合同](DATA_CONTRACT.md)、[架构](ARCHITECTURE.md)、[端到端案例](CASE_STUDY.md)、[来源清单](vendor-manifest.json)。

## 限制与边界

- 这是确定性、离线科研组件集成，未运行 LLM 访谈或内容生成；合成人群与媒体亲和度用于生成测试假设。
- 模拟随机实验仅演示估计与证据匹配机制，界面显示“模拟随机实验”；引擎从不赋予真实 `validated` 标签。真实推广前需要真实随机对照、样本量/MDE、数据质量和外部有效性检查。
- 预算反应曲线为显式情景假设，不是已校准的因果响应曲线。每个经营单元选一个场景和媒体动作，防止本单元重复计算；仍不覆盖跨 SKU、跨渠道用户重叠和蚕食。
- Price 建议属于独立经营测试，不进入媒体预算引擎；原型不会把优惠效果当作已经证实的营销增量。调拨与补货是建议，系统不会执行。
- 所有 EUR 为不含 VAT 的统一演示口径，无真实汇率换算。当前每周退货与该周销量匹配，返回商品隔离且不回可售库存。生产环境需要退货 cohort、可修复/可再售、残值与跨期延迟。
- 只支持连续完整周、统一币种和当前周规划；不处理权限、多人编辑、真实 PISI、广告 API、库存仓库分层或自动投放。
- `contract.py` 实现所用 schema 的有限关键字集合，不是通用 JSON Schema 引擎。新增 schema 关键字必须补充验证器或接入标准库。
