from pathlib import Path
import json,re,subprocess,time
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1]; OUT=R/'design/evidence'; OUT.mkdir(exist_ok=True)
URL='http://127.0.0.1:8873/'
results=[]
def check(name,fn):
 try:
  detail=fn();results.append({'test':name,'status':'pass','detail':detail});print('PASS',name,flush=True)
 except Exception as e:
  results.append({'test':name,'status':'fail','error':str(e)});print('FAIL',name,str(e)[:200],flush=True)
def require(ok,msg):
 if not ok:raise AssertionError(msg)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 def page_for(**opts):
  c=b.new_context(**opts);p=c.new_page();p.set_default_timeout(4500);p.set_default_navigation_timeout(15000);return c,p
 def static():
  html=(R/'dist/index.html').read_text();require(html==(R/'index.html').read_text(),'root differs from dist')
  require('document.write' not in html and 'fetchBuf(' not in html and not re.search(r'\bparts/',html),'runtime fragments')
  for i,(attrs,body) in enumerate(re.findall(r'<script\b([^>]*)>([\s\S]*?)</script>',html,re.I)):
   if 'src=' not in attrs and body.strip():
    q=subprocess.run(['node','--check'],input=body,text=True,capture_output=True);require(q.returncode==0,'JS syntax '+str(i)+q.stderr)
  source='\n'.join((R/x).read_text() for x in ['src/lab.html','inject.html','assets/lab.js','assets/modern.js','tools/deps.snapshot.json'])
  forbidden=[r'google-analytics\.com',r'googletagmanager\.com',r'\bgtag\s*\(',r'\bdataLayer\b',r'plausible\.io',r'umami\.is',r'posthog\.com',r'/api/(?:track|analytics)',r'\bvisitor[_-]?id\b',r'analytics[_-]?id']
  require(not any(re.search(p,source,re.I) for p in forbidden),'visitor analytics/tracking path restored')
  require("resultEl.innerHTML = '结果" not in (R/'parts/89.html').read_text(),'archived XSS persists')
  require('https://echarts.apache.org/zh/index.html' in (R/'tools/deps.snapshot.json').read_text(),'ECharts official URL missing from dependency snapshot')
  return 'root/dist byte-identical; inline scripts parse; no runtime parts; visitor analytics disabled; official ECharts URL snapshotted'
 check('static-and-syntax',static)
 def nojs():
  c,p=page_for(java_script_enabled=False);requests=[];p.on('request',lambda q:requests.append(q.url));p.goto(URL,wait_until='domcontentloaded');require(p.locator('section.demo').count()==56,'missing no-JS body');require(p.locator('.rail-link').count()==56,'missing no-JS nav');require(p.locator('noscript').is_visible(),'no-JS explanation missing');require(not any('/parts/' in q for q in requests),'fragment request');c.close();return '56 descriptions/prompts and 56 links visible without JavaScript'
 check('no-javascript',nojs)
 def viewport():
  data=[]
  for w,h in [(1440,1000),(1024,768),(768,1024),(390,844),(320,844)]:
   c,p=page_for(viewport={'width':w,'height':h});p.goto(URL,wait_until='domcontentloaded');p.wait_for_timeout(150)
   for theme in ['dark','light']:
    p.evaluate('(v)=>document.documentElement.dataset.theme=v',theme);require(p.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'overflow {w}/{theme}')
   p.keyboard.press('Tab');require(p.locator('.lab-skip').evaluate('(e)=>e===document.activeElement'),'skip link first');p.keyboard.press('Enter');require(p.locator('#main-content').evaluate('(e)=>e===document.activeElement'),'skip focus')
   data.append({'width':w,'themes':['dark','light'],'overflow':False});c.close()
  return data
 check('responsive-and-skip-link',viewport)
 def mobile_layers():
  details=[]
  for w in (390,320):
   c,p=page_for(viewport={'width':w,'height':844},is_mobile=True,has_touch=True);p.goto(URL,wait_until='domcontentloaded')
   sel='#demo-21';p.locator(sel).scroll_into_view_if_needed();p.wait_for_function("s=>['ready','error'].includes(document.querySelector(s)?.dataset.libState)",arg=sel,timeout=18000);state=p.locator(sel).get_attribute('data-lib-state');three_gap=None
   if state=='ready':
    toolbar=p.locator('#stage-21 .lab-equivalent-controls').bounding_box();canvas=p.locator('#stage-21 .three-box').bounding_box();require(toolbar is not None and canvas is not None and canvas['y']>=toolbar['y']+toolbar['height']+4,f'Three canvas overlaps toolbar at {w}px');three_gap=canvas['y']-(toolbar['y']+toolbar['height'])
   p.locator('#demo-22').scroll_into_view_if_needed();p.wait_for_timeout(160);canvas=p.locator('#stage-22 .p5-box').bounding_box();panel=p.locator('#stage-22 .p5-controls').bounding_box();require(canvas is not None and panel is not None and canvas['y']+canvas['height']<=panel['y']-2,f'p5 canvas overlaps settings at {w}px');details.append({'width':w,'three_gap':three_gap,'p5_gap':panel['y']-(canvas['y']+canvas['height'])});c.close()
  return details
 check('mobile-demo-layering',mobile_layers)
 def keyboard():
  c,p=page_for(viewport={'width':1440,'height':1000});p.goto(URL,wait_until='domcontentloaded')
  order=p.locator('#drag-list li').evaluate_all('(es)=>es.map(e=>e.dataset.label)');down=p.locator('#drag-list li').first.locator('.lab-sort-down');down.focus();p.keyboard.press('Enter');after=p.locator('#drag-list li').evaluate_all('(es)=>es.map(e=>e.dataset.label)');require(after[1]==order[0],'sort did not move');require(p.locator('#drag-list li').first.locator('.lab-sort-up').is_disabled(),'upper boundary');require(p.locator('#drag-status').inner_text().find('第 2 项')>=0,'sort announcement')
  tab=p.locator('#stage-11 .tab-btn').first;tab.focus();p.keyboard.press('End');require(p.locator('#stage-11 .tab-btn').last.get_attribute('aria-selected')=='true','End tab');require(p.locator('#stage-11 .tab-panel:not([hidden])').count()==1,'hidden panels');p.keyboard.press('Home');require(tab.get_attribute('aria-selected')=='true','Home tab')
  acc=p.locator('#stage-10 .acc-head').first;before_acc=acc.get_attribute('aria-expanded');acc.focus();p.keyboard.press('Enter');require(acc.get_attribute('aria-expanded')!=before_acc,'accordion aria');require(p.locator('#accordion-body-0').evaluate('(e)=>e.hidden')==(acc.get_attribute('aria-expanded')=='false'),'accordion hidden')
  anchor=p.locator('#anc-anchor');anchor.focus();before=anchor.evaluate('(e)=>e.getBoundingClientRect().left');p.keyboard.press('ArrowRight');require(anchor.evaluate('(e)=>e.getBoundingClientRect().left')>before,'anchor keyboard');p.keyboard.press('Home')
  p.locator('#lab-command-open').focus();p.keyboard.press('Enter');require(p.locator('#cmdk-mask').evaluate('(e)=>e.open'),'command dialog');p.locator('#cmdk-input').fill('不存在的演示');require(p.locator('#cmdk-empty').is_visible(),'command empty');p.keyboard.press('Escape');require(p.locator('#lab-command-open').evaluate('(e)=>e===document.activeElement'),'Escape return focus')
  p.locator('#search-input').fill('不会匹配任何结果');p.keyboard.press('Control+k');p.locator('#cmdk-input').fill('可调整分栏');require(p.locator('#cmdk-list [role=option]').count()==1,'command filter');p.keyboard.press('Enter');p.wait_for_timeout(100);require(p.locator('#demo-56').is_visible(),'command jump filtered');require(p.locator('#demo-56').evaluate('(e)=>e===document.activeElement'),'command target focus')
  c.close();return 'sort + boundaries/live status; tabs Home/End; accordion; anchor; native modal Escape/focus; real command navigation clears filters'
 check('keyboard-core-workflows',keyboard)
 def new_demos():
  c,p=page_for();p.goto(URL,wait_until='domcontentloaded');initial=p.locator('#undo-list li').evaluate_all('(es)=>es.map(e=>e.dataset.item)')
  for _ in range(3):p.locator('#undo-list .undo-remove').first.click()
  require(p.locator('#undo-list li').count()==0,'delete all')
  for _ in range(3):p.locator('#undo-last').click()
  require(p.locator('#undo-list li').evaluate_all('(es)=>es.map(e=>e.dataset.item)')==initial,'precise undo order');require(p.locator('#undo-last').is_disabled(),'undo boundary')
  p.locator('#undo-list .undo-remove').nth(1).click();p.locator('#undo-reset').click();require(p.locator('#undo-list li').count()==3,'reset')
  r=p.locator('#split-range');r.focus();p.keyboard.press('Home');require(r.input_value()=='15' and p.locator('#split-less').is_disabled(),'split lower bound');p.keyboard.press('End');require(r.input_value()=='85' and p.locator('#split-more').is_disabled(),'split upper bound');p.locator('#split-reset').click();require(r.input_value()=='50','split reset');require(p.locator('#split-layout').evaluate('(e)=>getComputedStyle(e).gridTemplateColumns').split()[0]==p.locator('#split-layout').evaluate('(e)=>getComputedStyle(e).gridTemplateColumns').split()[1],'grid ratio reset')
  c.close();return '3 consecutive removals precisely reversed; reset; range Home/End 15/85 + disabled boundaries + real grid 50/50'
 check('undo-and-split-keyboard',new_demos)
 def rejection():
  c,p=page_for();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
  p.add_init_script("Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new DOMException('denied','NotAllowedError')),readText:()=>Promise.reject(new DOMException('denied','NotAllowedError'))}});document.execCommand=()=>false;Storage.prototype.getItem=function(){throw new DOMException('denied','SecurityError')};Storage.prototype.setItem=function(){throw new DOMException('denied','SecurityError')};")
  p.goto(URL,wait_until='domcontentloaded');p.locator('#demo-01 .copy-btn').click();p.wait_for_timeout(150);require('拒绝' in p.locator('#toast-wrap').inner_text(),'copy false success');p.locator('#cl-copy').click();require('失败' in p.locator('#cl-out').inner_text(),'clipboard fallback false success');p.locator('#cl-read').click();p.wait_for_timeout(100);require('拒绝' in p.locator('#cl-out').inner_text(),'read rejection');p.locator('#share-run').click();p.wait_for_timeout(100);require('无法复制' in p.locator('#share-status').inner_text(),'share fallback false success');p.locator('#undo-list .undo-remove').first.click();require(p.locator('#undo-list li').count()==2,'storage blocks native feature');require(not errors,str(errors));c.close();return 'clipboard write/read and execCommand false are visible failures; denied storage does not stop native interactions'
 check('clipboard-and-storage-denied',rejection)
 def offline():
  c,p=page_for();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.add_init_script("""(()=>{const C=window.AudioContext||window.webkitAudioContext;if(!C)return;const f=C.prototype.createOscillator;C.prototype.createOscillator=function(){const n=f.call(this),s=n.start.bind(n);n.start=function(){window.__offlineOscillators=(window.__offlineOscillators||0)+1;return s.apply(n,arguments)};return n}})()""");c.route('**/*',lambda route:route.continue_() if route.request.url.startswith('http://127.0.0.1:8873/') or route.request.url.startswith('data:') else route.abort())
  p.goto(URL,wait_until='domcontentloaded')
  for n in (17,21,22,23,26):
   sel=f'#demo-{n:02d}';p.locator(sel).scroll_into_view_if_needed();p.wait_for_function("s=>document.querySelector(s)?.dataset.libState==='error'",arg=sel,timeout=6000);notice=p.locator(sel+' .lab-lib-notice');require(notice.is_visible(),f'{n}: explicit CDN error notice missing');require(notice.locator('button').is_enabled(),f'{n}: retry unavailable')
  p.locator('#p5-generate').click();require('未就绪' in p.locator('#p5-status').inner_text() or '失败' in p.locator('#p5-status').inner_text(),'p5 falsely claimed generation with CDN blocked')
  require(p.locator('#stage-23 a[href="https://echarts.apache.org/zh/index.html"]').count()==1,'official ECharts link unavailable offline')
  cell=p.locator('[data-voice="melody"] .seq-cell').first
  if 'is-on' not in (cell.get_attribute('class') or ''):cell.click()
  p.locator('#demo-28').scroll_into_view_if_needed();p.locator('#seq-play').click();p.wait_for_timeout(450);audio=p.locator('#seq-status').inner_text();osc=p.evaluate('window.__offlineOscillators||0')
  if 'Web Audio' in audio:require(osc>0,'Tone CDN blocked but no native oscillator started');p.locator('#seq-play').click();require('已停止' in p.locator('#seq-status').inner_text(),'native audio stop failed')
  else:require('浏览器未提供可用音频' in audio,'no truthful audio fallback status')
  p.locator('#undo-list .undo-remove').first.click();require(p.locator('#undo-list li').count()==2,'CDN blocked native feature');require(not errors,str(errors));c.close();return 'external origins blocked: GSAP/Three.js/p5/ECharts/Embla show retry errors; p5 reports no generation; Tone uses native Web Audio or explicit unsupported status; local controls remain available'
 check('all-external-dependencies-fail',offline)
 def xss():
  c,p=page_for();p.goto(URL,wait_until='domcontentloaded');sec=p.locator('#demo-36');sec.scroll_into_view_if_needed();p.wait_for_function("document.querySelector('#demo-36').dataset.libState==='ready'",timeout=18000)
  payloads=['<img src=x onerror="window.__labXss=1">','<svg onload="window.__labXss=2"></svg>','\"\'><b>literal</b>']
  for text in payloads:
   p.locator('#rx-input').fill(text);p.wait_for_timeout(1800);require(p.locator('#rx-result').inner_text().find(text)>=0,'query not literal');require(p.locator('#rx-result img,#rx-result svg').count()==0,'injected element');require(not p.evaluate('window.__labXss||false'),'payload ran')
  p.keyboard.press('Control+k');p.locator('#cmdk-input').fill(payloads[0]);require(p.locator('#cmdk-list img').count()==0,'command injection');p.keyboard.press('Escape');c.close();return 'img/onerror, svg/onload and quote/tag payloads remain literal text; no injected nodes or executed marker'
 check('user-input-xss',xss)
 def touch():
  c,p=page_for(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);p.goto(URL)
  label=p.locator('#drag-list li').first.get_attribute('data-label');p.locator('#drag-list li').first.locator('.lab-sort-down').tap();require(p.locator('#drag-list li').nth(1).get_attribute('data-label')==label,'touch sorting')
  p.locator('#undo-list .undo-remove').first.tap();require(p.locator('#undo-list li').count()==2,'touch remove');p.locator('#undo-last').tap();require(p.locator('#undo-list li').count()==3,'touch undo')
  p.locator('#split-more').tap();require(p.locator('#split-range').input_value()=='55','touch split button');r=p.locator('#split-range');r.scroll_into_view_if_needed();box=r.bounding_box();r.tap(position={'x':box['width']*.75,'y':box['height']/2});require(int(r.input_value())>55,'touch native range')
  images=p.locator('#cmp-wrap .cmp-image').evaluate_all('(xs)=>xs.map(x=>({src:x.currentSrc||x.src,complete:x.complete,width:x.naturalWidth}))');require(len(images)==2 and images[0]['src']==images[1]['src'] and all(x['complete'] and x['width']>0 for x in images),'#51 landscape image not loaded or shared by both comparison layers')
  cmp=p.locator('#cmp-range');cmp.scroll_into_view_if_needed();bb=cmp.bounding_box();cmp.tap(position={'x':bb['width']*.75,'y':bb['height']/2});require(int(cmp.input_value())>60,'touch comparison range')
  require(p.locator('#cmp-wrap .cmp-fallback-note').evaluate('(e)=>e.hidden'),'#51 stale fallback status is exposed after successful image decode')
  embla=p.locator('#embla-viewport');embla.scroll_into_view_if_needed();p.wait_for_function("document.querySelector('#demo-26')?.dataset.libState==='ready'",timeout=18000);before=p.locator('#embla-dot').inner_text();bb=embla.bounding_box();ecdp=c.new_cdp_session(p);sx=bb['x']+bb['width']*.82;ex=bb['x']+bb['width']*.18;ey=bb['y']+bb['height']/2;ecdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sx,'y':ey}]})
  for xx in [sx-45,sx-105,ex]:ecdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':xx,'y':ey}]});p.wait_for_timeout(45)
  ecdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_timeout(400);require(p.locator('#embla-dot').inner_text()!=before,'Embla horizontal touch swipe did not change slide')
  p.locator('#dlg-pop-btn').tap();require(p.locator('#dlg-pop').evaluate('(e)=>e.matches(":popover-open")'),'popover open');p.locator('#demo-48 h3').tap();require(not p.locator('#dlg-pop').evaluate('(e)=>e.matches(":popover-open")'),'popover light dismiss')
  canvas=p.locator('#draw-canvas');canvas.scroll_into_view_if_needed();p.wait_for_timeout(100);bb=canvas.bounding_box();before=canvas.evaluate('(e)=>e.toDataURL()');cdp=c.new_cdp_session(p);x=bb['x']+bb['width']*.3;y=bb['y']+bb['height']*.4
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
  for off in [10,25,45]:cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+off,'y':y+off/2}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});require(canvas.evaluate('(e)=>e.toDataURL()')!=before,'touch draw no pixels')
  p.evaluate('document.documentElement.style.scrollBehavior="auto";window.scrollTo(0,0)');p.wait_for_function('scrollY===0',timeout=3000);p.wait_for_timeout(120);scroll=p.evaluate('scrollY');sx=5
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sx,'y':700}]})
  for yy in [620,500,350]:cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':sx,'y':yy}]});p.wait_for_timeout(50)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_timeout(400);require(p.evaluate('scrollY')>scroll+80,'outside drawing blocks page scroll')
  c.close();return 'trusted touch: sorting, undo, split button/range, comparison, #26 Embla horizontal swipe, popover light-dismiss, canvas pixels changed; outside-canvas gesture scrolls page'
 check('real-touch-workflows',touch)
 def reduced():
  c,p=page_for(reduced_motion='reduce');p.goto(URL,wait_until='domcontentloaded');require(p.evaluate('matchMedia("(prefers-reduced-motion:reduce)").matches'),'system preference');p.locator('.lab-appearance summary').click();p.locator('#lab-motion-toggle').click();require(p.locator('html').get_attribute('data-motion')=='reduce','manual reduction');require(p.locator('.lab-primary').evaluate('(e)=>getComputedStyle(e).transitionDuration')=='0s','transitions still active');c.close();return 'system reduced-motion media and persisted manual CSS/transition reduction respected; no claim of full third-party GPU optimization'
 check('reduced-motion',reduced)
 b.close()
(OUT/'g3-robustness.json').write_text(json.dumps({'results':results,'passed':sum(x['status']=='pass' for x in results),'total':len(results),'all_pass':all(x['status']=='pass' for x in results)},ensure_ascii=False,indent=2)+'\n')
raise SystemExit(0 if all(x['status']=='pass' for x in results) else 1)
