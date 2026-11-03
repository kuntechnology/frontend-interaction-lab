from pathlib import Path
import json
from playwright.sync_api import sync_playwright
root = Path(__file__).resolve().parents[1]
out = root / 'design/evidence'
out.mkdir(parents=True, exist_ok=True)
results = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    for width,height,name in [(1440,1000,'desktop'),(390,844,'mobile'),(320,844,'small'),(768,1024,'tablet'),(1024,768,'laptop')]:
        page = b.new_page(viewport={'width':width,'height':height}, device_scale_factor=1)
        errors = []
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8873/design/prototype.html',wait_until='networkidle')
        missing = page.evaluate("""() => [...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash)""")
        overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth')
        page.keyboard.press('Tab')
        skip = page.locator('.lab-skip').evaluate('(e) => e===document.activeElement')
        page.keyboard.press('Enter')
        main_focus = page.locator('#main-content').evaluate('(e) => e===document.activeElement')
        page.evaluate('window.scrollTo(0,0); document.activeElement.blur()')
        min_nav = page.locator('.rail-link').evaluate_all('(nodes) => Math.min(...nodes.map(e=>e.getBoundingClientRect().height))')
        heading_valid = page.locator('h1').evaluate('(e) => e.parentElement.tagName === "DIV"')
        if name in ['desktop','mobile']:
            page.screenshot(path=str(out/f'g1-{name}.png'), full_page=False)
        results.append({'viewport':[width,height],'missing_anchors':missing,'overflow':overflow,'console_errors':errors,'skip_link_focus':skip,'main_focus':main_focus,'min_nav_height':min_nav,'heading_valid':heading_valid})
        page.close()
    b.close()
(out/'g1-browser.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
assert all(not r['missing_anchors'] and not r['overflow'] and not r['console_errors'] and r['skip_link_focus'] and r['main_focus'] and r['min_nav_height']>=44 and r['heading_valid'] for r in results)
