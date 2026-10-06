"""Weekly opportunity → audience → 4P → constrained budget → verification."""
import datetime as dt
import json
import math
from pathlib import Path
from adapters import inv, inv_schema, activation, population, channel_opportunities, evidence_activation
from contract import validate_input, validate_schema
ROOT=Path(__file__).resolve().parent
SIGNAL_SCHEMA=json.loads((ROOT/'vendor/audience-activation-spec/schemas/research-signal.schema.json').read_text())

def row_id(r):return '|'.join(r[k] for k in ('country','sku','channel','period'))

def unit_margin(r, discount=0):
    net_price=r['price_eur']*(1-discount)
    return_rate=r['returns_units']/r['sell_out_units'] if r['sell_out_units'] else 0
    # Refund full price, lose unit cost; returns stay quarantined. All EUR ex VAT.
    return net_price*(1-return_rate)*(1-r['channel_fee_pct'])-r['cost_eur']-return_rate*r['return_handling_eur']

def business(r, history):
    baseline=sum(x['sell_out_units']/x['seasonality_index'] for x in history)/len(history)*r['seasonality_index']
    daily=baseline/7
    inbound=r['inbound_units'] if r['inbound_due_days']<=7 else 0
    # No overselling before inbound arrives, even if weekly total looks sufficient.
    pre_eta=r['closing_stock_units']-daily*min(r['inbound_due_days'],7)
    headroom=max(0,min(r['closing_stock_units']+inbound-baseline,pre_eta)) if pre_eta>=0 else 0
    cover=r['closing_stock_units']/daily if daily else None
    rr=r['returns_units']/r['sell_out_units'] if r['sell_out_units'] else 0
    risks=[]
    if cover is not None and cover<r['lead_time_days']:risks.append('缺货风险')
    if cover is not None and cover>56:risks.append('积压风险')
    if rr>.10:risks.append('高退货')
    if not r['listed']:risks.append('未上市')
    margin=unit_margin(r)
    if margin<=0:risks.append('负贡献毛利')
    if headroom<=0:risks.append('促销无可售余量')
    promo_margin=unit_margin(r,r['discount_pct'])
    return {'baseline_units':baseline,'incremental_capacity_units':headroom,'days_cover':cover,'return_rate':rr,'unit_margin_eur':margin,'discount_margin_eur':promo_margin,'promo_viable':promo_margin>=r['price_eur']*.1,'risks':risks,'pre_inbound_stock_units':pre_eta}

def actions(r,b,scenario):
    blocked=any(x in b['risks'] for x in ['高退货','未上市','负贡献毛利','促销无可售余量'])
    return {'Product':('先排查安装、兼容与退货原因，再评估恢复投放' if '高退货' in b['risks'] else f"保留 {r['category']}，用 {scenario} 场景测试当地需求"),'Price':(f"可测试 {r['discount_pct']:.0%} 阶段优惠；优惠后单位贡献 €{b['discount_margin_eur']:.2f}；另立随机实验" if b['promo_viable'] and '积压风险' in b['risks'] and not blocked else '保持基准售价；未验证价格效果前不把折扣算作营销增量'),'Place':('先补货或同国调拨；在交期内锁定可售数量' if '缺货风险' in b['risks'] else '优先消化积压；评估同国渠道间调拨' if '积压风险' in b['risks'] else f"维持 {r['channel']} 上市，核查库存分配"),'Promotion':('暂停增长投放，先解除经营阻塞' if blocked else '先补本地语言商品页与门店演示' if r['content_readiness']<.6 else f'测试 {scenario} 素材与渠道代理人群')}

def evidence(r,scenario,media_channel,experiments,affinity):
    match=next((e for e in experiments if e['row_id']==row_id(r) and e['scenario']==scenario and e['media_channel']==media_channel),None)
    signal={'signal_id':row_id(r)+':'+scenario,'source_type':'synthetic_panel','audience_description':scenario,'finding':f'Fictional weighted affinity {affinity:.3f}','evidence_label':'preference_heterogeneity','calibration_level':'uncalibrated','limitations':['Fictional population and traits; hypothesis only, not consumer behavior.'],'recommended_use':'Design pilot and validate against randomized holdout.'}
    validate_schema(signal,SIGNAL_SCHEMA)
    if not match:return {'grade':'假设级','tau':.01*affinity,'tau_source':'expert_assumption','gate':None,'ci':None,'signal':signal,'basis':'fictional affinity scaled by explicit 0.01 planning assumption; no estimated causal effect'}
    pt=match['treatment_conversions']/match['treatment_n'];pc=match['control_conversions']/match['control_n']
    tau=pt-pc;se=math.sqrt(pt*(1-pt)/match['treatment_n']+pc*(1-pc)/match['control_n']);ci=[tau-1.96*se,tau+1.96*se]
    # Synthetic randomized design demonstrates mechanics; it never earns a real validated badge.
    signal={**signal,'signal_id':signal['signal_id']+':fixture-rct','source_type':'experiment','finding':f'Simulated treatment/control difference {tau:.4f}','evidence_label':'causal_hte','calibration_level':'experimentally_validated','limitations':['SIMULATED randomized fixture; no real experiment or external validity.'],'metadata':{'fictional':True,'design':match},'recommended_use':'Demonstrate randomized estimation only; run real holdout before scale.'}
    validate_schema(signal,SIGNAL_SCHEMA)
    return {'grade':'模拟随机实验','tau':max(0,ci[0]),'tau_point':tau,'tau_source':'modeled_hte','gate':None,'ci':ci,'signal':signal,'basis':'lower 95% normal CI of simulated arm difference, restricted to identical row/scenario/channel; not a real validated effect'}

def plan(data,budget=None,scenario_overrides=None,country='ALL',sku='ALL',channel='ALL'):
    validate_input(data)
    budget=data['planning_budget_eur'] if budget is None else budget
    if isinstance(budget,bool) or not isinstance(budget,(int,float)) or not math.isfinite(budget) or not 0<=budget<=100000:raise ValueError('budget must be finite EUR between 0 and 100000')
    scenario_overrides=scenario_overrides or {}
    if not isinstance(scenario_overrides,dict):raise ValueError('scenario_overrides must be object')
    latest=max(r['period'] for r in data['rows'])
    selected=[r for r in data['rows'] if r['period']==latest and (country=='ALL' or r['country']==country) and (sku=='ALL' or r['sku']==sku) and (channel=='ALL' or r['channel']==channel)]
    if not selected:raise ValueError('no current rows for selected filters')
    panels={};persona_artifacts={}
    for c,cells in data['population_cells'].items():persona_artifacts[c],panels[c]=population(cells)
    decisions=[];cells=[]
    for r in selected:
        rid=row_id(r);scenario=scenario_overrides.get(rid,r['scenario'])
        if scenario not in ('sport','commute','gift'):raise ValueError('unknown scenario')
        history=[h for h in data['rows'] if (h['country'],h['sku'],h['channel'])==(r['country'],r['sku'],r['channel']) and h['period']<=latest]
        b=business(r,history); opportunities=channel_opportunities(r,panels[r['country']],scenario)
        best=opportunities[0]
        # Match existing experiment's channel when available for this scenario.
        matching=next((e for e in data['experiments'] if e['row_id']==rid and e['scenario']==scenario),None)
        if matching:best=next((o for o in opportunities if o['channel_id']==matching['media_channel']),best)
        ev=evidence(r,scenario,best['channel_id'],data['experiments'],best['average_persona_affinity'])
        pop=sum(p['population_weight'] for p in panels[r['country']] if p['segment']==scenario)
        # Cap asymptotic incremental units by saleable headroom before optimization.
        reach=min(pop,b['incremental_capacity_units']/ev['tau']) if ev['tau']>0 else 0
        blockers=[x for x in b['risks'] if x in ('高退货','未上市','负贡献毛利','促销无可售余量')]
        if r['content_readiness']<.6:blockers.append('内容尚未就绪')
        if ev['ci'] and ev['ci'][0]<=0:blockers.append('模拟实验下界不为正')
        cell={'id':rid,'sku':rid,'module':'search' if best['channel_id']=='google_search' else 'retail_activation' if best['channel_id']=='ooh_local_events' else 'paid_social_video','channel':best['channel_id'],'tau_hat':ev['tau'],'tau_source':ev['tau_source'],'tau_basis':ev['basis'],'reachable_population':reach,'unit_margin':max(0,b['unit_margin_eur']),'max_spend':1500 if ev['grade']=='模拟随机实验' else 300,'saturation_k':.002,'readiness':0 if blockers else 1,'measurement_gate':None}
        d={'id':rid,'input':r,'business':b,'scenario':scenario,'evidence':ev,'actions':actions(r,b,scenario),'media_opportunities':opportunities,'media_selected':best['channel_id'],'blockers':blockers,'spend_eur':0,'incremental_units':0,'net_profit_eur':0,'next_action':'先解除阻塞' if blockers else '小额随机对照测试','owner':'国家GTM与渠道负责人','due':str(dt.date.fromisoformat(latest)+dt.timedelta(days=13))}
        d['activation']=evidence_activation(r,scenario,ev,best['channel_id'],blockers)
        decisions.append(d);cells.append(cell)
    eligible,blocked=inv.filter_investable_cells(cells,{c['sku']:'grow' for c in cells})
    cfg={'investment_plan':{'modules':[{'id':m} for m in sorted({c['module'] for c in cells})],'cells':cells,'total_budget':budget,'required_mroi':1.1}}
    inv_schema.validate_or_raise(cfg)
    allocation=inv.optimize_investment(eligible,budget,50,1.1)
    by_id={d['id']:d for d in decisions}
    for a in allocation['allocation']:
        d=by_id[a['sku']];d.update(spend_eur=a['spend'],incremental_units=a['units'],net_profit_eur=a['gross_profit']-a['spend'])
        if not d['blockers'] and not a['spend']:d['next_action']='保留预算，等待更强证据'
    for d in decisions:
        if d['spend_eur']==0 and not d['blockers']:d['next_action']='保留预算，等待更强证据'
    frontier=[{'budget':b,**{k:v for k,v in inv.optimize_investment(eligible,b,50,1.1).items() if k in ('recommended_spend','net_profit','incremental_units')}} for b in [0,1000,2500,5000,10000]]
    return {'fictional':True,'as_of':str(dt.date.fromisoformat(latest)+dt.timedelta(days=6)),'snapshot_period':latest,'decision_period':str(dt.date.fromisoformat(latest)+dt.timedelta(days=7)),'currency':'EUR','budget_eur':budget,'unspent_eur':budget-allocation['recommended_spend'],'allocation':allocation,'decisions':sorted(decisions,key=lambda d:-d['net_profit_eur']),'frontier':frontier,'personas':persona_artifacts,'lineage':{'population':'sample_persona_skeletons → actual sampled weights → simulate_one','activation':'generate_activation_plan','allocation':'investment_schema + filter_investable_cells + optimize_investment','evidence':'audience-activation-spec research-signal schema','business':'new weekly input contract + stock/margin/return constraints'},'notice':'全为虚构数据。亲和度是规则估计；利润是情景预测；模拟实验不代表真实因果证据。'}

def verify(result,outcomes):
    checks=[]
    for d in result['decisions']:
        o=next((o for o in outcomes if o['row_id']==d['id']),None)
        if not o:continue
        if o['period']<=result['as_of']:raise ValueError('outcome must follow decision period')
        r=d['input'];baseline=d['business']['baseline_units'];rr=o['returns_units']/o['sell_out_units'] if o['sell_out_units'] else 0
        contribution=o['sell_out_units']*(r['price_eur']*(1-rr)*(1-r['channel_fee_pct'])-r['cost_eur']-rr*r['return_handling_eur'])-o['marketing_spend_eur']
        checks.append({'id':d['id'],'label':o['label'],'planned_sell_out':baseline+d['incremental_units'],'simulated_sell_out':o['sell_out_units'],'delta_vs_baseline':o['sell_out_units']-baseline,'returns_rate':rr,'stock':o['closing_stock_units'],'contribution_after_marketing_eur':contribution,'causal_conclusion':'无法归因：此后测只有模拟经营结果，没有随机对照','next_action':'暂停并排查退货' if rr>.1 else '下周期补货' if o['closing_stock_units']<baseline else '保留假设并开展真实对照实验'})
    return checks
