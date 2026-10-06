"""Generate wholly fictional weekly consumer-electronics fixtures."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def make():
    rows=[]; populations={}; experiments=[]; outcomes=[]
    for ci,country in enumerate(['HU','RO','GR']):
        populations[country]=[{'cell_id':f'{country}-{s}','population_weight':w*(1+ci*.15),'hard':{'scenario':s,'traits':{'digital':d,'intent':i,'price':p,'premium':pr}},'calibration_trace':{'source':'fictional competition fixture; no census calibration'}} for s,w,d,i,p,pr in [('sport',12000,.85,.8,.4,.7),('commute',18000,.7,.7,.65,.45),('gift',9000,.6,.6,.45,.75)]]
        for si,(sku,category,price,cost) in enumerate([('NOVA-W1','smartwatch',169,90),('NOVA-B1','earbuds',89,38),('NOVA-T1','tablet',299,225)]):
            for channel in ['online','retail']:
                stock=190+ci*35+si*90
                if country=='GR' and sku=='NOVA-W1' and channel=='online':stock=155
                if country=='RO' and sku=='NOVA-B1' and channel=='retail':stock=1200
                for pi,period in enumerate(['2026-09-14','2026-09-21','2026-09-28']):
                    sold=38+ci*5+si*3+(8 if channel=='online' else 0)+pi*2
                    inbound=40 if pi==1 else 0
                    close=stock+inbound-sold
                    returns=8 if sku=='NOVA-T1' and country=='RO' else 2
                    r={'country':country,'sku':sku,'channel':channel,'period':period,'currency':'EUR','category':category,'price_eur':price,'cost_eur':cost,'channel_fee_pct':.08,'return_handling_eur':8,'opening_stock_units':stock,'sell_in_units':inbound,'sell_out_units':sold,'returns_units':returns,'closing_stock_units':close,'inbound_units':80,'inbound_due_days':5 if country=='HU' else 18,'lead_time_days':21,'discount_pct':.08 if sku=='NOVA-W1' else .15,'content_readiness':.8 if country=='HU' and sku=='NOVA-W1' else .45 if channel=='retail' else .8,'traffic_index':.4 if country=='RO' else .7,'listed':True,'marketing_spend_eur':250,'seasonality_index':1.0,'scenario':'sport' if si==0 else 'commute' if si==1 else 'gift','provenance':'fictional_fixture'}
                    rows.append(r);stock=close
                    if pi==2:
                        rid='|'.join([country,sku,channel,period])
                        outcomes.append({'row_id':rid,'period':'2026-10-05','sell_out_units':sold+9,'returns_units':returns,'closing_stock_units':max(0,close+(80 if r['inbound_due_days']<=7 else 0)-sold-9),'marketing_spend_eur':400,'label':'simulated_future_not_observed','randomized':False})
                        if country=='HU' and sku=='NOVA-W1':
                            experiments.append({'row_id':rid,'scenario':'sport','media_channel':'google_search' if channel=='online' else 'ooh_local_events','treatment_n':5000,'control_n':5000,'treatment_conversions':400,'control_conversions':200,'available_on':'2026-09-27','source':'simulated_randomized_fixture'})
    data={'contract_version':'1.0','fictional':True,'period_days':7,'planning_budget_eur':5000,'rows':rows,'population_cells':populations,'experiments':experiments}
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'data/demo.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/outcomes.json').write_text(json.dumps(outcomes,ensure_ascii=False,indent=2)+'\n')
    return data
if __name__=='__main__':make()
