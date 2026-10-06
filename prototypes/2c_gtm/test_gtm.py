import copy,json,math,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from engine import plan,business,unit_margin,verify,row_id
from contract import validate_input,validate_schema
from adapters import population,inv
from server import Handler,ThreadingHTTPServer,calculate,export
ROOT=Path(__file__).resolve().parent

class GTMTests(unittest.TestCase):
    def setUp(self):self.data=json.loads((ROOT/'data/demo.json').read_text())
    def bad(self,change):
        data=copy.deepcopy(self.data);change(data)
        with self.assertRaises(ValueError):validate_input(data)
    def test_full_closure(self):
        p=plan(self.data)
        self.assertEqual(len(self.data['rows']),54);self.assertEqual(len(p['decisions']),18)
        self.assertEqual(p['as_of'],'2026-10-04');self.assertEqual(p['decision_period'],'2026-10-05')
        self.assertLessEqual(p['allocation']['recommended_spend'],p['budget_eur'])
        self.assertAlmostEqual(sum(d['spend_eur'] for d in p['decisions']),p['allocation']['recommended_spend'])
        for d in p['decisions']:
            self.assertLessEqual(d['incremental_units'],d['business']['incremental_capacity_units']+1e-9)
            self.assertEqual(set(d['actions']),{'Product','Price','Place','Promotion'})
            if d['blockers']:self.assertEqual(d['spend_eur'],0)
            if d['evidence']['grade']=='假设级':self.assertLessEqual(d['spend_eur'],300)
    def test_duplicate_key(self):self.bad(lambda d:d['rows'].append(d['rows'][0]))
    def test_bad_reconciliation(self):self.bad(lambda d:d['rows'][0].update(closing_stock_units=0))
    def test_negative_stock(self):self.bad(lambda d:d['rows'][0].update(opening_stock_units=-1))
    def test_nonfinite(self):self.bad(lambda d:d['rows'][0].update(price_eur=math.nan))
    def test_boolean_price(self):self.bad(lambda d:d['rows'][0].update(price_eur=True))
    def test_bad_currency(self):self.bad(lambda d:d['rows'][0].update(currency='HUF'))
    def test_missing_population(self):self.bad(lambda d:d['population_cells'].pop('HU'))
    def test_stock_continuity(self):
        self.bad(lambda d:d['rows'][1].update(opening_stock_units=d['rows'][1]['opening_stock_units']+1,closing_stock_units=d['rows'][1]['closing_stock_units']+1))
    def test_future_experiment_leakage(self):self.bad(lambda d:d['experiments'][0].update(available_on='2026-10-10'))
    def test_bad_rct_counts(self):self.bad(lambda d:d['experiments'][0].update(treatment_conversions=99999))
    def test_quarantined_returns(self):
        r=self.data['rows'][0];self.assertEqual(r['closing_stock_units'],r['opening_stock_units']+r['sell_in_units']-r['sell_out_units'])
        r2={**r,'returns_units':r['sell_out_units']};self.assertLess(unit_margin(r2),0)
    def test_eta_is_not_weekly_free_stock(self):
        r=copy.deepcopy(self.data['rows'][-1]);r.update(closing_stock_units=1,inbound_units=10000,inbound_due_days=5)
        self.assertEqual(business(r,[r])['incremental_capacity_units'],0)
        r['closing_stock_units']=200;r['inbound_due_days']=18
        self.assertEqual(business(r,[r])['incremental_capacity_units'],200-r['sell_out_units'])
    def test_discount_margin_and_high_returns(self):
        p=plan(self.data)
        for d in p['decisions']:
            self.assertLessEqual(d['business']['discount_margin_eur'],d['business']['unit_margin_eur'])
            if d['input']['country']=='RO' and d['input']['sku']=='NOVA-T1':self.assertEqual(d['spend_eur'],0)
    def test_population_weights_actually_flow(self):
        personas,panel=population(self.data['population_cells']['HU'])
        self.assertEqual(len(personas),120)
        self.assertAlmostEqual(sum(p['population_weight'] for p in personas),39000)
        p=plan(self.data,country='HU')
        changed=copy.deepcopy(self.data)
        for cell in changed['population_cells']['HU']:cell['hard']['traits'].update(digital=.01,intent=.01,premium=.01,price=.99)
        q=plan(changed,country='HU')
        a={d['id']:d['media_opportunities'][0]['average_persona_affinity'] for d in p['decisions']}
        b={d['id']:d['media_opportunities'][0]['average_persona_affinity'] for d in q['decisions']}
        self.assertNotEqual(a,b)
    def test_audience_switch_invalidates_experiment(self):
        rid='HU|NOVA-W1|online|2026-09-28'
        p=plan(self.data,scenario_overrides={rid:'gift'})
        d=next(d for d in p['decisions'] if d['id']==rid)
        self.assertEqual(d['evidence']['grade'],'假设级');self.assertLessEqual(d['spend_eur'],300)
    def test_zero_budget(self):self.assertEqual(plan(self.data,budget=0)['allocation']['recommended_spend'],0)
    def test_budget_frontier_monotonic(self):
        front=plan(self.data)['frontier']
        self.assertEqual([f['net_profit'] for f in front],sorted(f['net_profit'] for f in front))
    def test_no_real_validated_badge(self):
        p=plan(self.data)
        self.assertTrue(all(s['confidence']!='validated' for s in p['allocation']['funded_steps']))
    def test_upstream_evidence_contract_blocks_synthetic_causality(self):
        from engine import SIGNAL_SCHEMA
        d=plan(self.data)['decisions'][-1];signal={**d['evidence']['signal'],'source_type':'synthetic_panel','evidence_label':'causal_hte'}
        with self.assertRaises(ValueError):validate_schema(signal,SIGNAL_SCHEMA)
    def test_outcomes_do_not_feed_planning(self):
        p=plan(self.data);o=json.loads((ROOT/'data/outcomes.json').read_text());v=verify(p,o)
        self.assertEqual(len(v),18);self.assertTrue(all('无法归因' in c['causal_conclusion'] for c in v))
        self.assertEqual(p,plan(self.data))
    def test_empty_selection_and_bad_budget(self):
        for opts in ({'country':'XX'},{'budget':-1},{'budget':float('inf')},{'budget':True}):
            with self.assertRaises(ValueError):plan(self.data,**opts)
    def test_vendor_hashes(self):
        import hashlib
        manifest=json.loads((ROOT/'vendor-manifest.json').read_text())
        for source in manifest['sources']:
            repo=source['repository'].split('/')[-1]
            for item in source['unchanged_files']:
                content=(ROOT/'vendor'/repo/item['path']).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(),item['sha256'])
    def test_nine_section_activation_plan(self):
        schema=json.loads((ROOT/'vendor/audience-activation-spec/schemas/activation-plan.schema.json').read_text())
        for d in plan(self.data)['decisions']:
            validate_schema(d['activation'],schema)
            self.assertNotIn('budget_allocation',d['activation'])
            self.assertEqual(d['activation']['measurement_and_instrumentation']['sales_channel'] if 'sales_channel' in d['activation']['measurement_and_instrumentation'] else d['activation']['channel_execution_specs'][0]['measurement']['sales_channel'],d['input']['channel'])
    def test_http_end_to_end(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            url=f'http://127.0.0.1:{server.server_port}'
            with urllib.request.urlopen(url) as r:self.assertIn('国家上市与营销经营',r.read().decode())
            req=urllib.request.Request(url+'/api/plan',data=json.dumps({'country':'HU','budget':500}).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req) as r:out=json.load(r)
            self.assertEqual(len(out['plan']['decisions']),6);self.assertLessEqual(out['plan']['allocation']['recommended_spend'],500)
            req=urllib.request.Request(url+'/api/plan',data=b'{"budget":-1}',headers={'Content-Type':'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(req)
            self.assertEqual(err.exception.code,400)
        finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
