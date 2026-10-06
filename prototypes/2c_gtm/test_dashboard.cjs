// Dependency-free DOM/API integration check. This is not a browser rendering test.
const assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm'), path=require('node:path'),{spawn}=require('node:child_process');
(async()=>{
 const proc=spawn(process.env.PYTHON||'python',[path.join(__dirname,'server.py'),'--port','8877']);
 try{
  await new Promise((resolve,reject)=>{proc.stdout.once('data',resolve);proc.once('exit',code=>reject(Error('server exited '+code)));proc.stderr.on('data',x=>process.stderr.write(x))});
  const nodes={};class Element{constructor(id){this.id=id;this.value=['country','sku','channel'].includes(id)?'ALL':id==='budget'?'5000':'';this.disabled=false;this.dataset={};this.html='';this.text=''}set innerHTML(v){this.html=v;this.children=null;if(this.id==='detail'){const options=[...v.matchAll(/<option value="(.*?)" (selected)?/g)];const chosen=options.find(x=>x[2]);if(chosen)get('audience').value=chosen[1]}}get innerHTML(){return this.html}set textContent(v){this.text=v}get textContent(){return this.text||this.html.replace(/<[^>]+>/g,' ')}querySelectorAll(){return this.children||(this.children=[...this.html.matchAll(/<tr data-id="(.*?)"/g)].map(x=>{const e=new Element('tr');e.dataset.id=x[1];return e}))}click(){this.onclick?.()}}
  const get=id=>nodes[id]||(nodes[id]=new Element(id));let last;
  const context={document:{getElementById:get,createElement:()=>new Element('a')},fetch:async(url,options)=>{const response=await fetch('http://127.0.0.1:8877'+url,options);const payload=await response.json();last=payload;return {ok:response.ok,json:async()=>payload}},Blob,URL,setTimeout,console};vm.createContext(context);
  const html=fs.readFileSync(path.join(__dirname,'dashboard.html'),'utf8');const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];vm.runInContext(script,context);
  const idle=async()=>{for(let n=0;n<200&&vm.runInContext('busy',context);n++)await new Promise(r=>setTimeout(r,10));assert.equal(vm.runInContext('busy',context),false);assert.equal(get('error').textContent,'')};await idle();assert.equal(last.plan.decisions.length,18);
  get('country').value='HU';await get('country').onchange();await idle();assert.equal(last.plan.decisions.length,6);
  const row=get('rows').querySelectorAll().find(x=>x.dataset.id==='HU|NOVA-W1|online|2026-09-28');row.onclick();get('audience').value='gift';get('audience').onchange();await idle();let d=last.plan.decisions.find(x=>x.id===row.dataset.id);assert.equal(d.scenario,'gift');assert.equal(d.evidence.grade,'假设级');assert.ok(d.spend_eur<=300);
  get('budget').value='0';await get('run').onclick();await idle();assert.equal(last.plan.allocation.recommended_spend,0);
  get('budget').value='-1';await get('run').onclick();assert.match(get('error').textContent,/budget/);
  console.log('PASS dashboard JavaScript + HTTP: initial load, country filter, audience recomputation, evidence downgrade, zero budget, error handling. Browser rendering not covered.');
 }finally{proc.kill()}
})().catch(e=>{console.error(e);process.exitCode=1});
