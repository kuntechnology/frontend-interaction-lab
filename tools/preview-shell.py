from pathlib import Path
import re, subprocess
from html import escape
root = Path(__file__).resolve().parents[1]
src = subprocess.check_output(['git', 'show', 'ed9a355:src/lab.html'], cwd=root).decode()
shell = (root / 'src/shell.html').read_text()
header = shell.split('<!-- HEADER -->')[1].split('<!-- /HEADER -->')[0]
intro = shell.split('<!-- INTRO -->')[1].split('<!-- /INTRO -->')[0]
rail = re.search(r'<aside\b[\s\S]*?</aside>', src).group()
rail = rail.replace('<nav ', '<p class="lab-rail-hint">演示目录 <span>左右滑动查看更多 →</span></p><nav ', 1)
sections = re.findall(r'<section class="demo"[\s\S]*?</section>', src)
stubs = []
for sec in sections:
    ident = re.search(r'id="(demo-\d+)"', sec).group(1)
    title = re.search(r'<h3>([\s\S]*?)</h3>', sec).group(1)
    desc = re.search(r'<p class="demo-desc">([\s\S]*?)</p>', sec).group(1)
    stubs.append(f'<section id="{ident}"><h3>{ident[5:]} / {title}</h3><p>{desc}</p></section>')
html = '<!doctype html>\n<html lang="zh-CN" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>前端交互实验室</title><link rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="../assets/lab.css"></head><body class="lab-shell">' + header + rail + '<main class="main">' + intro + '<div class="lab-prototype-demos">' + ''.join(stubs) + '<section id="matrix"><h3>框架对比矩阵</h3><p>框架、组件与数据流的不同选择。</p></section></div></main></body></html>\n'
(root / 'design/prototype.html').write_text(html)
print('Static shell built:', len(sections), 'existing demo anchors,',len(html.encode()),'bytes')
