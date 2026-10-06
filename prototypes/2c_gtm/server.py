"""Local dashboard server. Bind localhost; no credentials or external calls."""
import argparse,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from engine import plan,verify
ROOT=Path(__file__).resolve().parent

def load_data():return json.loads((ROOT/'data/demo.json').read_text())
def calculate(options):
    allowed={'budget','scenario_overrides','country','sku','channel'}
    if not isinstance(options,dict) or set(options)-allowed:raise ValueError('unknown plan options')
    result=plan(load_data(),**options)
    return {'plan':result,'verification':verify(result,json.loads((ROOT/'data/outcomes.json').read_text()))}

class Handler(BaseHTTPRequestHandler):
    def reply(self,status,body,kind='application/json'):
        raw=body.encode();self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if self.path in ('/','/dashboard.html'):self.reply(200,(ROOT/'dashboard.html').read_text(),'text/html')
        elif self.path=='/health':self.reply(200,'{"ok":true}')
        else:self.reply(404,'{"error":"not found"}')
    def do_POST(self):
        if self.path!='/api/plan':return self.reply(404,'{"error":"not found"}')
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=65536:raise ValueError('invalid request size')
            options=json.loads(self.rfile.read(length));result=calculate(options)
            self.reply(200,json.dumps(result,ensure_ascii=False,allow_nan=False))
        except (ValueError,TypeError,KeyError) as e:self.reply(400,json.dumps({'error':str(e)}))
    def log_message(self,*args):pass

def export(output):
    result=calculate({});output.mkdir(parents=True,exist_ok=True)
    (output/'decision.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    payload=json.dumps(result,ensure_ascii=False,allow_nan=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    (output/'dashboard.html').write_text((ROOT/'dashboard.html').read_text().replace('/*EMBEDDED*/null',payload))
    for country,personas in result['plan']['personas'].items():
        (output/(country+'-personas.jsonl')).write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in personas))
    print(json.dumps({'output':str(output),'recommended_spend':result['plan']['allocation']['recommended_spend'],'net_profit_scenario':result['plan']['allocation']['net_profit']},ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--export',type=Path);args=p.parse_args()
    if args.export:export(args.export)
    else:
        calculate({});print(f'2C GTM dashboard: http://127.0.0.1:{args.port}',flush=True)
        ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
