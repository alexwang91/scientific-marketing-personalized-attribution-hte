"""Pinned upstream adapters; upstream files remain unchanged."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / 'vendor'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

sm = VENDOR / 'scientific-marketing-personalized-attribution-hte'
if not sm.exists():
    sm = ROOT.parents[1]
syn = VENDOR / 'Synthetic-population-and-Silicon-sampling'
inv = load('gtm_investment', sm / '.claude/skills/sm-causal-personalization/scripts/investment_engine.py')
inv_schema = load('gtm_investment_schema', sm / '.claude/skills/sm-causal-personalization/scripts/investment_schema.py')
activation = load('gtm_activation', sm / 'skills/audience-activation/scripts/generate_activation_plan.py')
sampling = load('gtm_sampling', syn / 'skills/country-pack-builder/scripts/sample_persona_skeletons.py')
media = load('gtm_media', syn / 'skills/weighted-persona-pricing/scripts/generate_channel_plan.py')
simulation = load('gtm_simulation', syn / 'skills/weighted-persona-pricing/scripts/run_channel_simulation.py')

def population(cells):
    counts = sampling.allocate_largest_remainder([x['population_weight'] for x in cells], 120, min_one_per_positive_cell=True)
    personas = sampling.build_personas(cells, counts, id_prefix='FICTIONAL', id_width=4, start_index=1, allocation_method='largest_remainder')
    panel = []
    for p in personas:
        panel.append({'segment': p['hard']['scenario'], 'population_weight': p['population_weight'], **p['hard']['traits']})
    return personas, panel

def channel_opportunities(row, panel, segment):
    selected = [p for p in panel if p['segment'] == segment]
    plan = media.build_channel_plan({'country':row['country'], 'audience':segment, 'category':row['category'], 'product':row['sku'], 'budget':1000, 'currency':'EUR'})
    allowed = {'google_search','youtube','meta_ads'} if row['channel']=='online' else {'ooh_local_events','youtube','meta_ads'}
    results = []
    for c in plan['channels']:
        if c['channel_id'] not in allowed:
            continue
        # build_simulation() ignores personas at the pinned commit. Call its
        # leaf with our sampled panel instead. Do not use its default panel.
        r = simulation.simulate_one(c, 1000, selected, plan['input_brief'], {'average_order_value':row['price_eur'], 'target_population':sum(p['population_weight'] for p in selected)})
        r['creative_angle'] = {'sport':'展示运动记录和佩戴体验','commute':'展示通勤续航、兼容与便携','gift':'展示包装、质保和送礼场景'}[segment]
        r['evidence_label'] = 'preference_heterogeneity'
        r['limitations'] = ['Uncalibrated fictional personas; scenario bands are not statistical confidence intervals.']
        r.pop('confidence_interval', None)
        r.pop('confidence_level', None)
        results.append(r)
    return sorted(results, key=lambda x:-x['average_persona_affinity'])

def evidence_activation(row, scenario, evidence, selected_media, blockers):
    """Convert existing planner output to the evidence-aware nine-section spec.

    Upstream percentage profiles are intentionally excluded: only the profit
    engine owns actual budgets. The channels below are proxies, not identities.
    """
    from contract import validate_schema
    import json
    countries={'HU':'Hungary','RO':'Romania','GR':'Greece'}
    languages={'HU':'Hungarian','RO':'Romanian','GR':'Greek'}
    raw=activation.generate_plan({'country':countries[row['country']],'audience':scenario,'goal':'purchase','product_or_offer':row['sku'],'first_party_data':'none','language':languages[row['country']]})
    by_media={'google_search':'Google Search','youtube':'YouTube / video','meta_ads':'Meta Facebook / Instagram','ooh_local_events':'Partnerships / offline'}
    name=by_media[selected_media]
    spec=next((s for s in raw['channel_execution_specs'] if s['channel']==name),None)
    if spec is None:
        inp=raw['input'];ctx=raw['context']
        spec={'priority':'Low; pilot only','objective':'validate store activation','geography':ctx['region'],'language':ctx['language'],'audience_setup':activation.channel_proxy(name,inp,ctx),'landing_or_destination':activation.landing_destination(name,inp),'exclusions':activation.exclusions(name)}
    proxy=spec['audience_setup']
    test={'test_cell':'|'.join(row[k] for k in ('country','sku','channel','period'))+':'+scenario,'channel':name,'audience_proxy':proxy,'creative_angle':{'sport':'Sport usage demonstration','commute':'Commuting battery and compatibility','gift':'Gift packaging and warranty'}[scenario],'kpi':'incremental contribution after marketing; sell out; returns; stock','success_threshold':'95% randomized holdout lower bound on incremental profit > 0; return rate <= 10%; no stock block; preregister sample size before launch','next_action':'Resolve blockers before pilot' if blockers else 'Run capped holdout, then review next period'}
    plan={'activation_brief':{'country':countries[row['country']],'audience':scenario,'activation_thesis':raw['activation_brief']['activation_thesis'],'evidence_handling':'Fictional signals only. Synthetic preferences are hypotheses; simulated randomized fixtures never prove real efficacy.'},'market_and_channel_assumptions':[{'assumption':'fictional uncalibrated population','working_view':'scenario proxies may help formulate tests','confidence':'assumption grade','validation_needed':'real country population and randomized holdout'}],'mainstream_reach_channel_map':[{'channel':r['channel'],'role_in_funnel':r['funnel_role'],'why_it_fits_this_audience':r['why'],'reach_mechanism':r['audience_proxy'],'execution_priority':r['execution_priority']} for r in raw['channel_priority_map']],'research_signal_to_platform_mapping':[{'research_signal':evidence['signal']['signal_id'],'evidence_label':evidence['signal']['evidence_label'],'consumer_meaning':scenario+' usage hypothesis','platform_proxy':proxy,'channels_where_usable':name,'required_validation':'randomized treatment/control test within this country SKU sales channel and scenario','caveats':'proxy is not deterministic; simulated evidence is not real causal support'}],'channel_execution_specs':[{'channel':name,'role':spec['priority'],'objective':spec['objective'],'setup':{'geography':spec['geography'],'language':spec['language'],'audience_proxy':proxy,'creative_angle':test['creative_angle'],'landing_page':spec['landing_or_destination'],'exclusions':spec['exclusions']},'measurement':{'primary_kpi':test['kpi'],'sales_channel':row['channel'],'stock_gate':blockers,'utm_key':test['test_cell']},'evidence_basis':evidence['signal'],'validation_test':test['success_threshold']}],'experiment_matrix':[test],'measurement_and_instrumentation':{'design':'randomize eligible users or non-overlapping stores; log assignment before exposure','holdout':'50/50 test/control within selected cell; choose one audience/media action per row to avoid double-counting','duration':'at least two complete weeks, after sample-size and MDE review; continue if underpowered','primary_metric':'net contribution after marketing','guardrails':'returns <=10%, stock capacity, no cross-cell attribution claims','deduplication':'country/SKU/sales-channel/period key; person-level deduplication remains a production requirement'},'prioritized_launch_plan':[{'owner':'country GTM lead','task':'resolve stock/content/service blocks, then preregister and run pilot','blocked_by':blockers}],'quality_checks':['Fictional data explicitly labeled','Evidence schema validated','No synthetic causal claim','No deterministic targeting','No real platform activation','Actual budget owned by constrained profit engine']}
    schema=json.loads((VENDOR/'audience-activation-spec/schemas/activation-plan.schema.json').read_text())
    validate_schema(plan,schema)
    return plan
