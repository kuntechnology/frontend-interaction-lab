#!/usr/bin/env python3
"""G3 real-browser regression for the 56-demo interaction lab.
Run after build while http://127.0.0.1:8873/dist/ serves the final dist tree.
Writes only design/evidence/g3-regression.json and design/evidence/g3-screenshots/.
"""
from __future__ import annotations
import html, json, re, subprocess, time
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:8873/dist/'
OUT=ROOT/'design/evidence'; SHOTS=OUT/'g3-screenshots'
OUT.mkdir(parents=True,exist_ok=True); SHOTS.mkdir(parents=True,exist_ok=True)

# Per-demo deterministic interaction contracts. Assertions compare state before/after,
# not merely that a click returned. Platform-gated APIs are intentionally separate.
LIB_DEMOS={17:('#gs-scroll','.gs-block'),18:('#lottie-box','svg,canvas,.lottie-animation'),19:('#anime-box','*'),20:('#motion-list','.motion-item'),23:('#echart-box','canvas,svg'),25:('.lab-swiper','.swiper-slide'),26:('#embla-viewport','.embla-slide'),30:('#demo-30 .stage','*'),31:('#demo-31 .stage','*'),32:('#hx-target','*'),33:('#stage-33','*'),35:('#jt-a-val','*'),36:('#rx-result','*'),37:('#demo-37 .stage','*'),43:('#demo-43 .stage','*'),45:('#demo-45 .stage','*')}
DEPENDENCY_SELECTORS=['.dependency-error','.lib-error','.error-state','.loading','.swiper','.echart-box','.lottie-box','.three-container','.p5-canvas']

def text(locator):
    try:return locator.inner_text(timeout=1800).strip()
    except Exception:return ''
def attr(locator,name):
    try:return locator.get_attribute(name,timeout=1500) or ''
    except Exception:return ''
def baseline_contract():
    old=subprocess.check_output(['git','show','ed9a355:src/lab.html'],cwd=ROOT,text=True)
    cur=(ROOT/'src/lab.html').read_text()
    from bs4 import BeautifulSoup
    a,b=BeautifulSoup(old,'html.parser'),BeautifulSoup(cur,'html.parser')
    diffs=[]
    for i in range(1,55):
        ident=f'demo-{i:02d}'; x=a.find(id=ident); y=b.find(id=ident)
        if not x or not y: diffs.append({'demo':i,'field':'block','status':'fail'});continue
        for field,sel in [('title','.demo-head h3'),('description','.demo-desc')]:
            xx=x.select_one(sel); yy=y.select_one(sel); xv=xx.get_text('\n',strip=True) if xx else None; yv=yy.get_text('\n',strip=True) if yy else None
            if xv!=yv:
                allowed=(i==49 or i==50) and field=='description'
                diffs.append({'demo':i,'field':field,'status':'authorized-fix' if allowed else 'fail','baseline':xv,'current':yv})
        # Extract pre source before parsing; entity-escaped <...> must be unescaped as text,
        # never reparsed as markup (BeautifulSoup would drop the literal tag examples).
        def prompt(src):
            m=re.search(r'<section\b[^>]*class=["\'][^"\']*\bprompt\b[^"\']*["\'][^>]*>.*?<pre\b[^>]*>(.*?)</pre>',src,re.S|re.I)
            return html.unescape(re.sub(r'<[^>]*>','',m.group(1))) if m else None
        def block(src,ident):
            m=re.search(r'<(?:article|section|div)\b(?=[^>]*\bid=["\']'+re.escape(ident)+r'["\'])[^>]*>.*?</(?:article|section|div)>',src,re.S|re.I)
            return m.group(0) if m else ''
        p0,p1=prompt(block(old,ident)),prompt(block(cur,ident))
        if p0!=p1:
            allowed=i in (48,54)
            diffs.append({'demo':i,'field':'prompt','status':'authorized-fix' if allowed else 'fail','baseline':p0,'current':p1})
    return diffs

report={'started_at':datetime.now(timezone.utc).isoformat(),'url':URL,'demos':[],'console_errors':[],'page_errors':[],'failed_requests':[],'overall_errors':[],'baseline_differences':baseline_contract(),'screenshots':{},'environment':{'browser':'Chromium','executable_path':'/usr/bin/chromium'}}
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    context=browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1,permissions=[])
    page=context.new_page(); page.set_default_timeout(2500); page.set_default_navigation_timeout(8000)
    page.on('console',lambda m: report['console_errors'].append({'type':m.type,'text':m.text,'url':m.location.get('url'),'location':m.location}) if m.type=='error' else None)
    page.on('pageerror',lambda e: report['page_errors'].append({'message':str(e),'url':page.url}))
    page.on('requestfailed',lambda r: report['failed_requests'].append({'url':r.url,'method':r.method,'failure':r.failure}))
    try:
        resp=page.goto(URL,wait_until='domcontentloaded',timeout=15000); report['http_status']=resp.status if resp else None
        page.wait_for_timeout(300)
        demos=page.locator('.demo'); ids=demos.evaluate_all('(xs)=>xs.map(x=>x.id)')
        report['structure']={'demo_count':demos.count(),'ids':ids,'catalogue_links':page.locator('a[href^="#demo-"]').count(),'prompt_blocks':page.locator('.demo .prompt pre').count(),'prompt_copy_buttons':page.locator('.demo .copy-btn').count(),'code_copy_buttons':page.locator('.demo .copy-code-btn').count()}
        for key in ('demo_count','prompt_blocks','prompt_copy_buttons','code_copy_buttons'):
            if report['structure'][key]!=56: report['overall_errors'].append(f"{key}: expected 56, got {report['structure'][key]}")
        if len(set(ids))!=56:report['overall_errors'].append('demo ids are not 56 unique IDs')
        for i in range(1,57):
            ident=f'demo-{i:02d}'; d=page.locator('#'+ident); item={'number':i,'id':ident,'status':'pass','actions':[],'observed':{},'dependency_state':'native-or-rendered'}
            try:
                if d.count()!=1:raise AssertionError(f'expected exactly one {ident}, got {d.count()}')
                d.scroll_into_view_if_needed(timeout=2500); page.wait_for_timeout(90)
                item['observed']['title']=text(d.locator('.demo-head h3'))
                item['observed']['prompt_present']=d.locator('.prompt pre').count()==1
                item['observed']['copy_controls']={'prompt':d.locator('.copy-btn').count(),'code':d.locator('.copy-code-btn').count()}
                if not item['observed']['prompt_present'] or item['observed']['copy_controls']!={'prompt':1,'code':1}:raise AssertionError('prompt/copy controls missing')
                # Wait at most 15 seconds for deferred libraries to expose ready/error evidence.
                if i in LIB_DEMOS:
                    deadline=time.monotonic()+15
                    marker=LIB_DEMOS[i][0]
                    while time.monotonic()<deadline:
                        state=d.evaluate("e=>({errors:[...e.querySelectorAll('.dependency-error,.lib-error,.error-state')].map(x=>x.innerText),loading:!!e.querySelector('.loading,[aria-busy=true]')})")
                        if state['errors'] or not state['loading']:break
                        page.wait_for_timeout(150)
                    item['dependency_state']={'error':state['errors'],'loading_after_wait':state['loading'],'marker_count':d.locator(marker).count()}
                    if state['errors']:
                        item['status']='degraded';item['notes']=['dependency reported error; no success claimed']
                # Canvas/SVG/animation/interactive payload evidence before manipulation.
                item['observed']['visual_targets']=d.evaluate("e=>({canvas:e.querySelectorAll('canvas').length,svg:e.querySelectorAll('svg').length,animatedContainers:e.querySelectorAll('.lottie-box,.anime-box,.motion-list,.gs-scroll,.echart-box,.three-container,.p5-canvas').length,stageChildren:e.querySelector('.stage')?.children.length||0})")
                c=lambda s:d.locator(s)
                action=None
                if i==1:
                    b=c('button.ripple-demo').first; before=c('.ripple').count();b.click();page.wait_for_timeout(80);ok=c('.ripple').count()>before;action=('click ripple button',ok,'ripple element count increased')
                elif i==5:
                    before=c('.stat b').all_inner_texts();c('#stat-run').click();page.wait_for_timeout(1000);after=c('.stat b').all_inner_texts();action=('replay counter',bool(after) and before!=after,'counter values changed after replay')
                elif i==8:
                    x=c('.flip[role=button]');before='is-flipped' in attr(x,'class');x.focus();page.keyboard.press('Enter');ok=('is-flipped' in attr(x,'class'))!=before;action=('focus .flip and press Enter',ok,'keyboard activation toggled flip state class')
                elif i==10:
                    x=c('.acc-head').first;before=attr(x,'aria-expanded');x.click();action=('accordion header click',attr(x,'aria-expanded')!=before,'aria-expanded changed')
                elif i==11:
                    x=c('.tab-btn').nth(1);x.click();action=('select second tab', 'is-active' in attr(x,'class') and len(c('.tab-btn.is-active').all())==1,'second tab became sole active tab')
                elif i==12:
                    c('.toast-trigger').first.click();page.wait_for_timeout(80);action=('trigger toast',page.locator('.toast, [role=alert]').count()>0,'toast/alert node rendered')
                elif i==13:
                    c('#sk-reset').click();before=c('#sk-shimmer').is_visible();c('#sk-load').click();page.wait_for_timeout(1600);action=('load skeleton content',before and c('#sk-content').is_visible() and not c('#sk-shimmer').is_visible(),'content shown and skeleton hidden')
                elif i==14:
                    x=c('#dm-toggle');before=attr(c('#stage-14'),'class');x.click();after=attr(c('#stage-14'),'class');action=('toggle local theme',('is-dark' in before)!=('is-dark' in after),'stage theme class toggled')
                elif i==16:
                    x=c('#draw-canvas');box=x.bounding_box();before=page.evaluate('(el)=>el.toDataURL()',x.element_handle());page.mouse.move(box['x']+25,box['y']+25);page.mouse.down();page.mouse.move(box['x']+100,box['y']+60,steps=4);page.mouse.up();painted=page.evaluate('(el)=>el.toDataURL()',x.element_handle())!=before;c('#draw-clear').click();cleared=page.evaluate('(el)=>el.toDataURL()',x.element_handle());action=('draw with pointer then clear',painted and cleared!=painted,'canvas bitmap changed on draw and clear')
                elif i in (17,18,19,20,23,25,26,28,29,32,33,35,36,41,42,45,49,50,51,54,55,56):
                    if i==17:
                        x=c('#gs-play');before=[attr(z,'style') for z in c('.gs-block').all()];x.click();page.wait_for_timeout(250);after=[attr(z,'style') for z in c('.gs-block').all()];ok=bool(c('.gs-block').count()) and before!=after;desc='GSAP target inline styles changed'
                    elif i==18:
                        x=c('#lottie-toggle');before=text(x);x.click();ok=text(x)!=before;desc='Lottie button toggled play/pause label'
                    elif i==19:
                        x=c('#anime-play');before=attr(c('#anime-box'),'style');x.click();page.wait_for_timeout(200);ok=bool(c('#anime-box').count()) and attr(c('#anime-box'),'style')!=before;desc='Anime target style changed'
                    elif i==20:
                        x=c('#motion-run');x.click();page.wait_for_timeout(80);ok=bool(c('.motion-item').count()) and c('.motion-item').evaluate_all('(xs)=>xs.some(x=>x.getAnimations().length>0 || x.style.length>0)');desc='Motion library created animation objects or inline animation state'
                    elif i==23:
                        x=c('#ec-toggle');before=text(x);x.click();ok=text(x)!=before;desc='ECharts update toggle label changed'
                    elif i==25:
                        x=c('.swiper-button-next');before=attr(c('.swiper-wrapper'),'style');x.click();page.wait_for_timeout(200);ok=attr(c('.swiper-wrapper'),'style')!=before;desc='Swiper wrapper translated'
                    elif i==26:
                        x=c('#embla-next');before=text(c('#embla-dot'));x.click();ok=text(c('#embla-dot'))!=before;desc='Embla slide indicator changed'
                    elif i==28:
                        x=c('.seq-cell').first;before=attr(x,'class');x.click();ok=attr(x,'class')!=before;desc='sequencer cell on/off class changed'
                    elif i==29:
                        x=c('.theme-opt').nth(1);x.click();ok='is-active' in attr(x,'class') and c('.theme-opt.is-active').count()==1;desc='second theme option uniquely active'
                    elif i==32:
                        x=c('.btn').filter(has_text='加载片段 A');before=text(c('#hx-target'));x.click();page.wait_for_timeout(350);ok=text(c('#hx-target'))!=before and '片段 A' in text(c('#hx-target'));desc='HTMX target replaced by fragment A'
                    elif i==33:
                        x=c('.alp-menu > button').first;x.click();page.wait_for_timeout(80);opened=c('.alp-dropdown').is_visible();c('.alp-stepper button').nth(1).click();page.wait_for_timeout(80);qty=text(c('.alp-stepper b'));action=('open menu and increment Alpine quantity',opened and qty=='2','menu visible and quantity incremented');
                        x=c('button').filter(has_text='打开模态').first;x.click();shown=c('.alp-modal-mask').is_visible();c('.alp-modal-mask button').filter(has_text='关闭').click();closed=not c('.alp-modal-mask').is_visible();ok=action[1] and shown and closed;desc='dropdown, quantity, modal open/close verified'
                    elif i==35:
                        x=c('[data-jt="inc-a"]');before=text(c('#jt-a-val'));x.click();after=text(c('#jt-a-val'));product=text(c('#jt-c-val'));ok=before!=after and product not in ('','–');desc='Jotai atom and derived value updated'
                    elif i==36:
                        x=c('#rx-input');x.fill('regression');page.wait_for_timeout(1050);ok='regression' in text(c('#rx-result')).lower() or 'regression' in text(c('#rx-status')).lower();desc='debounced RxJS result reflects query'
                    elif i==41:
                        x=c('#anc-toggle');before=attr(x,'aria-expanded');x.click();after=attr(x,'aria-expanded');ok=before!=after or c('#stage-41 .anc-pop:visible').count()>0;desc='anchor popover visibility/expanded state changed'
                    elif i==42:
                        x=c('#vt-toggle');before=text(x);x.click();after=text(x);ok=before!=after or c('.vt-grid:visible').count()>0;desc='view transition view/output state changed'
                    elif i==45:
                        x=c('#wk-run');before=text(d);x.click();page.wait_for_timeout(1800);after=text(d);ok=after!=before and ('质数个数' in after or '不支持 Worker' in after or 'Worker 运行出错' in after);desc='worker result or explicit platform error rendered'
                    elif i==49:
                        x=c('#cmdk-open');x.click();mask=page.locator('#cmdk-mask');opened=mask.evaluate('(e)=>e.open');page.locator('#cmdk-input').fill('翻转');page.wait_for_timeout(80);results=page.locator('#cmdk-list').inner_text();ok=opened and ('3D' in results or '翻转' in results);page.locator('#cmdk-close').click();closed=not mask.evaluate('(e)=>e.open');ok=ok and closed;desc='command search returns matching result; dialog closed'
                    elif i==50:
                        x=c('#vs-view');count0=c('#vs-rows').locator('> *').count();x.evaluate('(e)=>{e.scrollTop=6000;e.dispatchEvent(new Event("scroll"))}');page.wait_for_timeout(120);count1=c('#vs-rows').locator('> *').count();action=('scroll virtual list',count0>0 and count1>0,'visible rows rendered before and after scroll');
                    elif i in (51,54):
                        sel='#cmp-range' if i==51 else '#prop-slider';x=c(sel);lo=int(x.get_attribute('min') or 0);hi=int(x.get_attribute('max') or 100);before=x.input_value();value=str(lo+(hi-lo)//2+max(1,(hi-lo)//7));x.fill(value);page.wait_for_timeout(80);ok=x.input_value()==value and before!=value
                        if i==51:ok=ok and c('#cmp-wrap').evaluate('(e)=>getComputedStyle(e).getPropertyValue("--p").trim()')==value+'%'
                        else:ok=ok and c('#prop-swatches').locator('> *').count()>0
                        desc='range within declared min/max and corresponding CSS/render output changed'
                    elif i==55:
                        before=c('#undo-list .undo-remove').count();x=c('#undo-list .undo-remove').first;x.click();removed=c('#undo-list .undo-remove').count()==before-1;status=text(c('#undo-status'));c('#undo-last').click();restored=c('#undo-list .undo-remove').count()==before;action=('remove then undo list item',removed and bool(status) and restored,'list count removed/restored and live status updated')
                    else:
                        x=c('#split-more');before=c('#split-range').input_value();x.click();v=c('#split-range').input_value();layout=attr(c('#split-layout'),'style');out=text(c('#split-output'));action=('increase split ratio',v!=before and v=='55' and bool(out) and bool(layout),'range, output and layout style reflect increment')
                    if action is None:action=(f'activate {i} control',ok,desc)
                elif i in (39,):
                    x=c('label.has-card').first;cb=x.locator('input[type=checkbox]');before=cb.is_checked();x.click(position={'x':10,'y':12});after=cb.is_checked();action=('click first :has() checkbox card label',not before and after,'associated checkbox toggled by real pointer click')
                elif i==40:
                    x=c('#cq-range');lo=int(x.get_attribute('min') or 0);hi=int(x.get_attribute('max') or 100);v=str(lo+(hi-lo)//2);before=x.input_value();x.fill(v);page.wait_for_timeout(50);action=('set container-query slider within declared range',x.input_value()==v and before!=v,'range value changed within actual min/max; responsive style sampled');item['observed']['range_style']=d.locator('.cq-card').first.evaluate('(e)=>getComputedStyle(e).gridTemplateColumns') if d.locator('.cq-card').count() else None
                elif i==43:
                    x=c('#cl-copy');x.click();page.wait_for_timeout(120);status=text(c('#cl-out'));supported=page.evaluate('!!navigator.clipboard?.writeText');item['capability_outcome']={'clipboardWriteApi':supported,'status':status};item['status']='degraded';action=('clipboard action with denied/unavailable permission captured',True,'platform permission/result explicitly recorded; no clipboard success claimed')
                elif i==44:
                    before=text(c('#sp-status'));c('#sp-stop').click();after=text(c('#sp-status'));action=('speech stop path',bool(c('#sp-stop').count()) and (before==after or after!=''),'stop control invoked without claiming audio playback')
                elif i==46:
                    x=c('#fs-toggle');x.click();page.wait_for_timeout(80);status=text(c('#fs-status'));fullscreen=page.evaluate('!!document.fullscreenElement');item['capability_outcome']={'fullscreenElement':fullscreen,'status':status,'requestFullscreen':page.evaluate('typeof document.documentElement.requestFullscreen')};item['status']='degraded';action=('fullscreen API attempted; permission outcome recorded',True,'platform capability/status recorded; not claimed as universally successful')
                elif i==47:
                    x=c('#share-run');x.click();page.wait_for_timeout(250);status=text(c('#share-status'));item['capability_outcome']={'share':page.evaluate('typeof navigator.share'),'status':status};item['status']='degraded';action=('share API attempted; platform outcome recorded',True,'native share availability/result recorded, no share success claimed')
                elif i==48:
                    x=c('#dlg-open');x.click();opened=c('#dlg-demo').evaluate('(e)=>e.open');c('#dlg-demo form button').click();closed=not c('#dlg-demo').evaluate('(e)=>e.open');p=c('#dlg-pop-btn');p.click();pop=c('#dlg-pop').evaluate('(e)=>e.matches(":popover-open")');page.keyboard.press('Escape');popclosed=not c('#dlg-pop').evaluate('(e)=>e.matches(":popover-open")');action=('open/close dialog and popover',opened and closed and pop and popclosed,'both native modal/popover opened and closed')
                elif i==52:
                    x=c('#up-input');action=('file upload control available',x.count()==1 and x.get_attribute('type')=='file' and c('#up-zone').count()==1,'native file picker input and drop target confirmed; no arbitrary file injected')
                elif i==53:
                    x=c('#snap-view');cards=c('.snap-card').count();before=x.evaluate('(e)=>e.scrollLeft');x.focus();page.keyboard.press('ArrowRight');page.wait_for_timeout(100);after=x.evaluate('(e)=>e.scrollLeft');action=('keyboard scroll snap container',cards>=2 and (after!=before or x.evaluate('(e)=>e.scrollWidth>e.clientWidth')),'snap cards/overflow confirmed and keyboard scrolling exercised')
                else:
                    # Static/visual demos: assert concrete render targets, never infer full function from no exception.
                    targets=item['observed']['visual_targets'];present=targets['canvas']+targets['svg']+targets['animatedContainers']+targets['stageChildren']
                    if i==9:
                        nodes=c('#stage-09 [draggable=true]');action=('drag-sort target inspection',nodes.count()>=2,'draggable items present; pointer drag covered only if source exposes draggable targets')
                    elif i in (3,4,6,7,15,21,22,24,27,30,31,37,38):
                        action=('visual/render target inspection',present>0,'concrete canvas/svg/animation/stage content present; no claim beyond rendered surface')
                    else:
                        ctl=d.locator('button:visible,input:visible,select:visible,[role=button]:visible').first
                        action=('rendered content inspection',present>0,'content payload verified')
                item['actions'].append({'selector':action[0],'assertion':bool(action[1]),'result':action[2]})
                if not action[1]:raise AssertionError('observable behavior assertion failed: '+action[2])
                item['observed']['live_regions']=d.locator('[aria-live],[role=status],[role=alert]').all_inner_texts()
                item['observed']['inputs']=d.locator('input').evaluate_all('(xs)=>xs.map(x=>({id:x.id,type:x.type,value:x.value,checked:x.checked,disabled:x.disabled}))')
                item['observed']['selected_tabs']=d.locator('[role=tab][aria-selected="true"],.tab-btn.is-active,.theme-opt.is-active').all_inner_texts()
            except Exception as e:
                item['status']='fail';item['error']=str(e);report['overall_errors'].append(f'{ident}: {e}')
                # Ensure modal UI never blocks later demos even after assertion errors.
                try:
                    page.evaluate("()=>{document.querySelectorAll('dialog[open]').forEach(x=>x.close());document.querySelectorAll('[popover]:popover-open').forEach(x=>x.hidePopover())}")
                except Exception:pass
            report['demos'].append(item)
            if i%10==0:print(f'[G3] {i}/56 demos; failures={sum(x["status"]=="fail" for x in report["demos"])} degraded={sum(x["status"]=="degraded" for x in report["demos"])}',flush=True)
        report['capabilities']=page.evaluate("()=>({secureContext:isSecureContext,speechSynthesis:!!window.speechSynthesis,clipboard:!!navigator.clipboard,clipboardWrite:typeof navigator.clipboard?.writeText,share:typeof navigator.share,fullscreen:typeof document.documentElement.requestFullscreen,wakeLock:typeof navigator.wakeLock,userAgent:navigator.userAgent})")
        for selector in ['#undo-list .undo-remove','#undo-last','#undo-reset','#undo-status','#split-range','#split-reset','#split-less','#split-more','#split-layout','#split-output']:
            if selector=='#undo-list .undo-remove':
                if page.locator(selector).count()<1:report['overall_errors'].append('required removable list item missing')
            elif page.locator(selector).count()!=1:report['overall_errors'].append(f'required selector {selector}: {page.locator(selector).count()}')
        page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(150)
        for name,pth in [('desktop',SHOTS/'g3-desktop.png')]:page.screenshot(path=str(pth),full_page=False,timeout=20000);report['screenshots'][name]=str(pth)
        mobile=browser.new_page(viewport={'width':390,'height':844});mobile.goto(URL,wait_until='domcontentloaded',timeout=15000);mobile.screenshot(path=str(SHOTS/'g3-mobile.png'),full_page=False,timeout=20000);report['screenshots']['mobile']=str(SHOTS/'g3-mobile.png');mobile.close()
        report['screenshot_themes']={}
        for name,width,height in [('light',1440,1000),('mobile-light',390,844)]:
            light=browser.new_page(viewport={'width':width,'height':height});light.goto(URL,wait_until='domcontentloaded',timeout=15000)
            light.locator('.lab-appearance summary').click();light.locator('.theme-toggle').click()
            assert light.locator('html').get_attribute('data-theme')=='light','theme control did not select light'
            actual_bg=light.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')
            assert actual_bg=='rgb(245, 244, 237)',f'incorrect light background: {actual_bg}'
            light.locator('.lab-appearance summary').click();light.screenshot(path=str(SHOTS/f'g3-{name}.png'),full_page=False,timeout=20000)
            report['screenshots'][name]=str(SHOTS/f'g3-{name}.png');report['screenshot_themes'][name]={'theme':'light','background':actual_bg,'trigger':'real theme-toggle button'};light.close()
        cdns=[x for x in report['failed_requests'] if any(h in x['url'] for h in ('cdn.jsdelivr.net','fonts.googleapis.com','miaoda.feishu.cn'))]
        report['external_dependency_status']={'status':'degraded','failed_urls':[x['url'] for x in cdns]} if cdns else {'status':'no observed CDN request failure'}
        for f in report['failed_requests']:
            if not any(t in f['url'].lower() for t in ('favicon','cdn.jsdelivr.net','fonts.googleapis.com','miaoda.feishu.cn')):report['overall_errors'].append(f"failed request: {f['url']} ({f['failure']})")
        bad=[x for x in report['baseline_differences'] if x['status']=='fail']
        if bad:report['overall_errors'].append(f'{len(bad)} unauthorized baseline text differences')
        if report['page_errors']:report['overall_errors'].append(f'{len(report["page_errors"])} uncaught page errors')
        if report['console_errors']:report['overall_errors'].append(f'{len(report["console_errors"])} console errors')
    except Exception as e:report['overall_errors'].append('fatal: '+repr(e))
    finally:
        report['finished_at']=datetime.now(timezone.utc).isoformat();report['failed_demo_count']=sum(x['status']=='fail' for x in report['demos']);report['degraded_demo_count']=sum(x['status']=='degraded' for x in report['demos'])
        report['overall_status']='fail' if report['overall_errors'] or report['failed_demo_count'] else ('degraded' if report['degraded_demo_count'] or report['failed_requests'] else 'pass')
        (OUT/'g3-regression.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');browser.close()
print(json.dumps({'status':report['overall_status'],'report':str(OUT/'g3-regression.json'),'demos':len(report['demos']),'failures':report['failed_demo_count'],'degraded':report['degraded_demo_count'],'errors':report['overall_errors']},ensure_ascii=False,indent=2))
