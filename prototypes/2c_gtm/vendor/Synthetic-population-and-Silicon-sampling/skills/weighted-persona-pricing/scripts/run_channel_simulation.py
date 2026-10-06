#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from datetime import datetime, timezone
from pathlib import Path

def load_json(p):
    v=json.loads(Path(p).read_text(encoding='utf-8-sig'))
    if not isinstance(v, dict): raise ValueError('expected object')
    return v

def write_json(p,v):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def num(x,d=0.0):
    try:
        return d if x is None or isinstance(x,bool) else float(x)
    except Exception:
        return d

def aov(brief, assumptions):
    if num(assumptions.get('average_order_value'))>0: return num(assumptions.get('average_order_value'))
    cat=str(brief.get('category','')).lower()
    return 249.0 if 'watch' in cat or 'wearable' in cat else 120.0

def market(brief, assumptions):
    if num(assumptions.get('target_population'))>0: return num(assumptions.get('target_population'))
    return 114800.0 if str(brief.get('country','')).lower()=='hungary' else 100000.0

def fallback_panel():
    return [
        {'segment':'high_intent_cycling_tech','population_weight':26000,'digital':.92,'intent':.86,'price':.42,'premium':.72},
        {'segment':'premium_performance_seekers','population_weight':18000,'digital':.82,'intent':.74,'price':.34,'premium':.88},
        {'segment':'price_sensitive_commuters','population_weight':21000,'digital':.66,'intent':.58,'price':.82,'premium':.36},
        {'segment':'health_tracking_mainstream','population_weight':28000,'digital':.72,'intent':.62,'price':.56,'premium':.54},
        {'segment':'local_event_discoverers','population_weight':14000,'digital':.48,'intent':.45,'price':.62,'premium':.42},
    ]

def score(row, cid, stage):
    d,i,p,pr=[num(row.get(k),.5) for k in ['digital','intent','price','premium']]
    if cid in {'google_search','retail_media','affiliate','email_sms'}: s=.42*i+.28*d+.18*(1-p)+.12*pr
    elif cid in {'meta_ads','youtube','tiktok_ads','programmatic_display'}: s=.35*d+.25*i+.20*pr+.20*(1-p*.45)
    else: s=.26*i+.22*pr+.20*(1-p)+.18*(1-d)+.14
    return max(.05,min(.98,s*{'awareness':.55,'consideration':.75,'conversion':1.0}.get(stage,.75)))

def allocate(channels,total):
    w={}
    for c in channels:
        w[c['channel_id']]=max(.01,num(c.get('estimated_reach_quality'),.5)*(0.55+num(c.get('scale_index'),.5))/max(num(c.get('cost_index'),1),.1))
    s=sum(w.values()) or 1
    return {k:total*v/s for k,v in w.items()}

def simulate_one(c,budget,panel,brief,assumptions):
    cid, stage = c['channel_id'], c.get('funnel_stage','consideration')
    q, scale, cost = num(c.get('estimated_reach_quality'),.5), num(c.get('scale_index'),.5), max(num(c.get('cost_index'),1),.1)
    order=aov(brief,assumptions); pop=market(brief,assumptions)
    cpm=(5.5+10.5*cost)/max(.55+scale,.1)
    impressions=max(1,budget/cpm*1000)
    reach=min(pop*(.18+.82*scale), impressions*(.46+.32*q))
    top=[]; total=0; weighted=0
    for r in panel:
        wt=max(num(r.get('population_weight'),1),0); aff=score(r,cid,stage); total+=wt; weighted+=aff*wt
        top.append({'segment':r.get('segment','segment'),'affinity':round(aff,3),'weighted_population':round(wt,2)})
    aff=weighted/total if total else .5
    ctr=max(.001,min(.09,.006+.032*q*aff)); cvr=max(.001,min(.14,.012+.09*aff/max(cost,.1)))
    clicks=impressions*ctr; conv=min(reach*.18, clicks*cvr); revenue=conv*order
    cac=budget/conv if conv else None; roas=revenue/budget if budget else 0; roi=(revenue-budget)/budget if budget else 0
    band=.18+.18*(1-q)+(.12 if c.get('risk_level')=='high' else .04)
    top.sort(key=lambda x:(-x['affinity'],-x['weighted_population']))
    return {'channel_id':cid,'name':c.get('name'),'funnel_stage':stage,'allocated_budget':round(budget,2),'estimated_reach':round(reach,0),'impressions':round(impressions,0),'clicks':round(clicks,0),'weighted_conversions':round(conv,2),'estimated_revenue':round(revenue,2),'cac':round(cac,2) if cac else None,'roas':round(roas,3),'roi':round(roi,3),'confidence_interval':[round(roi-band,3),round(roi+band,3)],'confidence_level':'directional_80pct','average_persona_affinity':round(aff,3),'top_segments':top[:5],'top_drivers':['fit','intent','measurement'],'top_risks':['uncalibrated estimate','scale limit','attribution noise'],'simulation_basis':'weighted_persona_scoring'}

def build_simulation(plan, personas=None, budget=None, assumptions=None):
    assumptions=assumptions or {}; brief=plan.get('input_brief',{}); total=budget if budget is not None else num(brief.get('budget'))
    if total<=0: raise ValueError('budget must be positive')
    channels=plan.get('channels') or []
    if not channels: raise ValueError('channel_plan must contain channels')
    panel=fallback_panel(); alloc=allocate(channels,total)
    rows=[simulate_one(c,alloc[c['channel_id']],panel,brief,assumptions) for c in channels]
    rows.sort(key=lambda r:(-num(r.get('roi')),-num(r.get('weighted_conversions')),r.get('channel_id')))
    return {'channel_simulation_version':'0.1.0','generated_at':datetime.now(timezone.utc).isoformat(),'input_brief':brief,'panel_source':'generated_weighted_archetypes','panel_summary':{'record_count':len(panel),'total_weighted_population':sum(num(r.get('population_weight')) for r in panel),'activation_policy':'full panel deterministic scoring; medium and deep layers are optional explanation layers','llm_dependency':'none_by_default'},'budget_assumptions':{'total_budget':total,'currency':brief.get('currency') or 'EUR','average_order_value':aov(brief,assumptions),'target_population':market(brief,assumptions)},'channel_results':rows,'limitations':['Planning estimates are not observed campaign performance.']}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('channel_plan',type=Path); p.add_argument('--personas',type=Path); p.add_argument('--budget',type=float); p.add_argument('--assumptions',type=Path); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    out=build_simulation(load_json(a.channel_plan),personas=a.personas,budget=a.budget,assumptions=load_json(a.assumptions) if a.assumptions else {})
    write_json(a.output,out); print(json.dumps({'channel_count':len(out['channel_results']),'output':str(a.output)},ensure_ascii=False,indent=2)); return 0
if __name__=='__main__':
    raise SystemExit(main())
