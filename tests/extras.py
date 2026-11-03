from pathlib import Path
import json,base64,hashlib
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];URL='http://127.0.0.1:8873/dist/';out=[]
def need(ok,msg):
 if not ok:raise AssertionError(msg)
def test(name,fn):
 try:detail=fn();out.append({'test':name,'status':'pass','detail':detail});print('PASS',name,flush=True)
 except Exception as e:out.append({'test':name,'status':'fail','error':str(e)});print('FAIL',name,str(e)[:250],flush=True)
def lum(rgb):
 v=[x/255 for x in rgb[:3]];v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v];return sum(x*y for x,y in zip(v,[.2126,.7152,.0722]))
def ratio(a,b):
 x,y=sorted([lum(a),lum(b)]);return (y+.05)/(x+.05)
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 def new(**opts):
  c=b.new_context(**opts);p=c.new_page();p.set_default_timeout(6000);p.goto(URL,wait_until='domcontentloaded');return c,p
 def retry():
  c=b.new_context();p=c.new_page();p.set_default_timeout(6000);attempt=[]
  def intercept(route):
   attempt.append(route.request.url)
   if len(attempt)==1:route.abort()
   else:route.continue_()
  c.route('**/gsap.min.js',intercept);p.goto(URL,wait_until='domcontentloaded');p.locator('#demo-17').scroll_into_view_if_needed();p.locator('#demo-17 .lab-lib-notice button').wait_for();p.locator('#demo-17 .lab-lib-notice button').click();p.wait_for_function("document.querySelector('#demo-17').dataset.libState==='ready'",timeout=20000);need(len(attempt)==2,'retry request count');need(p.locator('#demo-17 .lab-lib-notice').count()==0,'failure notice persisted after recovery');p.locator('#gs-play').click();p.wait_for_timeout(100);need(p.evaluate('typeof gsap.timeline')=='function','actual GSAP interface');c.close();return 'first actual GSAP request blocked, explicit retry fetched real CDN chain; initialized once and removed error notice'
 test('real-cdn-retry-recovery',retry)
 def copying():
  c,p=new(permissions=['clipboard-read','clipboard-write'])
  for no in ['55','56','49']:
   p.locator('#demo-'+no+' .copy-code-btn').click();p.locator('#demo-'+no+' .copy-code-btn.is-done').wait_for();text=p.evaluate('navigator.clipboard.readText()');need('/* ===== '+no in text,'missing JS/CSS marker '+no);need('<style>' in text and '<script>' in text,'missing source chunks '+no)
   if no=='49':need('id="cmdk-mask"' in text,'portal dialog missing from copied code')
  p.locator('#demo-55 .copy-btn').click();text=p.evaluate('navigator.clipboard.readText()');need('精确' in text and '撤销' in text,'prompt copy not source');c.close();return 'actual clipboard contains CSS+JS for 55/56, real native dialog markup for 49, correct prompt text'
 test('real-code-and-prompt-copy',copying)
 def filters():
  c,p=new();p.locator('#filter-bar button').filter(has_text='工作流').click();p.locator('#search-input').fill('可撤销');need(p.locator('.demo:visible').count()==1,'combined filter count');need(p.locator('#demo-55').is_visible(),'combined result');saved=p.url;p.reload(wait_until='domcontentloaded');need(p.locator('.demo:visible').count()==1 and p.locator('#demo-55').is_visible(),'URL state not restored');p.locator('#search-input').fill('');p.locator('#filter-bar button').filter(has_text='全部').first.click();need(p.locator('.demo:visible').count()==56,'clear filters');c.close();return {'filtered_url':saved,'restored_demo':'55','cleared_count':56}
 test('filter-url-roundtrip',filters)
 def contrast():
  c,p=new();data=[]
  for theme in ['dark','light']:
   for accent in ['orange','cyan','violet','lime']:
    p.evaluate('([t,a])=>{document.documentElement.dataset.theme=t;document.documentElement.dataset.accent=a}',[theme,accent])
    values=p.evaluate("""() => {const rgb=s=>s.match(/[\\d.]+/g).map(Number);const bg=rgb(getComputedStyle(document.body).backgroundColor);return ['.lead','.lab-facts','.lab-brand small','.lab-category-foot','.lab-primary'].map(sel=>{const e=document.querySelector(sel),s=getComputedStyle(e);return{selector:sel,fg:rgb(s.color),bg:sel==='.lab-primary'?rgb(s.backgroundColor):bg}})}""")
    ratios=[{'selector':v['selector'],'ratio':round(ratio(v['fg'],v['bg']),2)} for v in values];need(all(x['ratio']>=4.5 for x in ratios),'shell contrast '+theme+'/'+accent+str(ratios));data.append({'theme':theme,'accent':accent,'ratios':ratios})
  c.close();return data
 test('shell-actual-eight-theme-contrast',contrast)
 def targets():
  values=[]
  for width in [1440,390,320]:
   c,p=new(viewport={'width':width,'height':1000});m=p.locator('.rail-link,#filter-bar button,.lab-primary,.lab-text-link,.lab-command-trigger,.lab-appearance summary').evaluate_all('(es)=>Math.min(...es.filter(e=>e.getClientRects().length).map(e=>e.getBoundingClientRect().height))');need(m>=44,'target too small '+str((width,m)));values.append({'width':width,'minimum_height':m});c.close()
  return values
 test('navigation-touch-targets',targets)
 def upload():
  c,p=new();img=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=');p.locator('#up-input').set_input_files({'name':'fixture.png','mimeType':'image/png','buffer':img});p.wait_for_function("document.querySelector('#up-preview').complete && document.querySelector('#up-preview').naturalWidth===1");need(p.locator('#up-preview').get_attribute('src').startswith('blob:'),'preview uploaded remotely');c.close();return 'one-pixel local fixture decodes from a blob URL; no remote upload endpoint used'
 test('local-image-preview',upload)
 def wake():
  c,p=new();p.locator('#wl-toggle').click();p.wait_for_timeout(300);native=p.locator('#wl-status').inner_text();need(bool(native),'wake lock has no status')
  if p.locator('#wl-toggle').inner_text()=='释放常亮':
   p.locator('#wl-toggle').click();p.wait_for_timeout(150);need('释放' in p.locator('#wl-status').inner_text(),'release not reflected')
  c.close();c=b.new_context();p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.add_init_script("Object.defineProperty(navigator,'wakeLock',{value:{request:()=>Promise.reject(new DOMException('denied','NotAllowedError'))}})");p.goto(URL,wait_until='domcontentloaded');p.locator('#wl-toggle').click();p.wait_for_timeout(100);need('失败' in p.locator('#wl-status').inner_text(),'wake denial not visible');need(not errors,str(errors));c.close();return {'native_outcome':native,'forced_permission_denial':'visible failure, no uncaught error'}
 test('wake-lock-capability-and-denial',wake)
 def privacy():
  need('lab-meta.yagook.workers.dev' not in (R/'dist/index.html').read_text(),'tracking origin still in runtime');need('setInterval' not in (R/'inject.html').read_text(),'stats polling persists')
  c=b.new_context();p=c.new_page();requests=[];p.on('request',lambda q:requests.append(q.url));p.add_init_script("localStorage.setItem('lab_vid','legacy-test-id')");p.goto(URL,wait_until='domcontentloaded');p.wait_for_timeout(500);need(p.evaluate("localStorage.getItem('lab_vid')") is None,'old identifier not removed');need(not any('lab-meta.yagook.workers.dev' in url for url in requests),'tracking request observed');c.close();return 'no tracking origin or poll in production; pre-existing test identifier removed locally; zero stats requests observed'
 test('no-visitor-tracking-or-stats-request',privacy)
 b.close()
(R/'design/evidence/g3-extras.json').write_text(json.dumps({'results':out,'all_pass':all(x['status']=='pass' for x in out)},ensure_ascii=False,indent=2)+'\n')
raise SystemExit(0 if all(x['status']=='pass' for x in out) else 1)
